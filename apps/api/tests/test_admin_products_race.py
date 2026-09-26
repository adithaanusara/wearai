import threading

from sqlalchemy import Engine, text
from sqlalchemy.orm import Session

from app.models import Product, User
from app.seed import load_catalogue
from app.services import admin_products
from app.services.admin import AdminError

# No catalogue fixture here: that one keeps uncommitted rows open in another transaction, and this
# test commits real rows from separate connections.
TEE = "w-tee-01"


def test_two_admins_editing_at_the_same_moment_cannot_both_win(engine: Engine) -> None:
    """A real race on separate connections: the row lock makes the second see the first."""
    with Session(engine) as setup:
        load_catalogue(setup)
        admins = [
            User(name=n, email=f"race-{n}@example.com", password_hash="x", role="admin")
            for n in ("a", "b")
        ]
        setup.add_all(admins)
        setup.commit()
        actor_ids = [a.id for a in admins]
        version = setup.get(Product, TEE).updated_at

    outcomes: list[str] = []
    start = threading.Barrier(2)

    def act(actor_id: int, price: int) -> None:
        with Session(engine) as session:
            actor = session.get(User, actor_id)
            start.wait()
            try:
                admin_products.edit_product(
                    session,
                    actor=actor,
                    product_id=TEE,
                    expected_updated_at=version,
                    changes={
                        "name": "Essential Fitted Tee",
                        "price": price,
                        "compare_at_price": None,
                        "description": session.get(Product, TEE).description,
                    },
                )
                outcomes.append("ok")
            except AdminError as error:
                outcomes.append(str(error.code))

    try:
        threads = [
            threading.Thread(target=act, args=(actor_ids[0], 3300)),
            threading.Thread(target=act, args=(actor_ids[1], 3400)),
        ]
        for thread in threads:
            thread.start()
        for thread in threads:
            thread.join()

        assert sorted(outcomes) == ["ok", "stale_product"]
    finally:
        with Session(engine) as cleanup:
            # DELETE on the audit log is refused by design; the disposable test database is emptied.
            cleanup.execute(text("TRUNCATE audit_log"))
            cleanup.execute(text("DELETE FROM users WHERE email LIKE 'race-%@example.com'"))
            cleanup.execute(text("DELETE FROM products"))
            cleanup.commit()
