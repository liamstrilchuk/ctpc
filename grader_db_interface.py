import time, requests

from app import app
from models import Submission, SubmissionStatus, TestCaseStatus, db

GRADER_URL = "http://127.0.0.1:8000"

def check_submissions():
	pending_submissions = Submission.query.filter_by(
		status_id=SubmissionStatus.query.filter_by(name="Pending").first().id
	).all()

	pending_submission_ids = [sub.id for sub in pending_submissions]

	response = requests.post(GRADER_URL + "/get-submission-statuses", json={
		"submissions": pending_submission_ids
	}).json()

	pending_status = TestCaseStatus.query.filter_by(name="Pending").first().id
	accepted_status = TestCaseStatus.query.filter_by(name="Accepted").first().id

	for ps in pending_submissions:
		if not str(ps.id) in response:
			continue

		all_completed = True
		total_points = 0
		for tcg in ps.test_case_groups:
			all_correct = True

			for tc in tcg.test_cases:
				if str(tc.id) in response[str(ps.id)]:
					tc.status_id = TestCaseStatus.query.filter_by(name=response[str(ps.id)][str(tc.id)]["status"]).first().id
					tc.output = response[str(ps.id)][str(tc.id)]["output"]

				if not tc.status_id == accepted_status:
					all_correct = False

				if tc.status_id == pending_status:
					all_completed = False

			if all_correct:
				total_points += tcg.abstract_group.point_value
				tcg.points_earned = tcg.abstract_group.point_value

		if all_completed:
			ps.status_id = SubmissionStatus.query.filter_by(name="Completed").first().id
			ps.points_earned = total_points

	db.session.commit()

def main():
	while True:
		try:
			with app.app_context():
				check_submissions()
		except Exception as e:
			print(f"Error when fetching submissions: {e}")

		time.sleep(2)

if __name__ == "__main__":
	main()