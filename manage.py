def deploy():
	from app import setup_app, db
	from flask_migrate import upgrade, migrate, init, stamp
	
	app = setup_app()
	app.app_context().push()

	if input("Are you sure you want to delete all tables and data? (y/n) ").lower() == "y":
		db.drop_all()
	db.create_all()

	init()
	stamp()
	migrate()
	upgrade()

	from models import User, School, SchoolBoard
	from flask_bcrypt import Bcrypt

	bcrypt = Bcrypt()
	user = User(username="admin", password=bcrypt.generate_password_hash("admin"), role="admin")
	db.session.add(user)

	board = SchoolBoard(name="Waterloo Region District School Board")
	db.session.add(board)
	db.session.commit()

	school = School(name="Preston High School", school_board_id=board.id)
	db.session.add(school)

	school = School(name="Waterloo Collegiate Institute", school_board_id=board.id)
	db.session.add(school)

	db.session.commit()

deploy()