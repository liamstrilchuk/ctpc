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

	from models import User, School, SchoolBoard, TestCaseStatus, UserRole, ContestType, SubmissionStatus, LanguageType
	from flask_bcrypt import Bcrypt

	test_case_statuses = ["Pending", "Accepted", "Wrong Answer", "Time Limit Exceeded", "Memory Limit Exceeded", "Runtime Error", "Compilation Error", "Failed"]

	for tcs in test_case_statuses:
		status = TestCaseStatus(name=tcs)
		db.session.add(status)

	submission_statuses = ["Pending", "Accepted", "Failed"]

	for tcs in submission_statuses:
		status = SubmissionStatus(name=tcs)
		db.session.add(status)

	roles = ["admin", "teacher", "student"]

	for role in roles:
		user_role = UserRole(name=role)
		db.session.add(user_role)

	contest_types = ["team", "individual"]

	for contest_type in contest_types:
		ct = ContestType(name=contest_type)
		db.session.add(ct)

	language_types = [("Python", "py"), ("C++", "cpp"), ("Java", "java"), ("C", "c"), ("JavaScript", "js")]

	for language_type in language_types:
		lt = LanguageType(name=language_type[0], short_name=language_type[1])
		db.session.add(lt)

	db.session.commit()

	bcrypt = Bcrypt()
	user = User(
		username="admin",
		password=bcrypt.generate_password_hash("admin"),
		role_id=UserRole.query.filter_by(name="admin").first().id
	)
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