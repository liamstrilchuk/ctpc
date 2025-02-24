import models, csv
import handle_objects
from app import app

def main():
	lines = []
	with open("school_data/teacher_emails.csv", "r") as f:
		reader = csv.reader(f)

		for line in reader:
			lines.append(line)

	with app.app_context():
		competition = models.Competition.query.filter_by(short_name="2025").first()

		for line in lines:
			board = models.SchoolBoard.query.filter_by(name=line[1]).first()

			if board is None:
				board = models.SchoolBoard(name=line[1])
				models.db.session.add(board)
				models.db.session.commit()

			code = handle_objects.add_school_code(board.id, competition.id, line[2])
			line.append(code)
			print(f"{line[2]} has code {code}")

	with open("school_data/teacher_emails_with_codes.csv", "w") as f:
		writer = csv.writer(f)
		writer.writerows(lines)

if __name__ == "__main__":
	main()