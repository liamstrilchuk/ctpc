from fastapi import Request, FastAPI
from fastapi.middleware.cors import CORSMiddleware
import threading, requests, math

from grader_models import Submission, TestCase

GRADER_URLS = ["http://localhost:2358"]
current_grader = 0
current_submissions = {}
pending_testcases = {}
total_submissions = 0

app = FastAPI()
app.add_middleware(
	CORSMiddleware,
	allow_origins=["*"],
	allow_credentials=True,
	allow_methods=["*"],
	allow_headers=["*"]
)
STATUSES = {
	"Pending": ["In Queue", "Processing"],
	"Accepted": ["Accepted"],
	"Wrong Answer": ["Wrong Answer"],
	"Time Limit Exceeded": ["Time Limit Exceeded"],
	"Compilation Error": ["Compilation Error"],
	"Runtime Error": ["Runtime Error (SIGSEGV)", "Runtime Error (SIGXFSZ)", "Runtime Error (SIGFPE)", "Runtime Error (SIGABRT)", "Runtime Error (NZEC)", "Runtime Error (Other)"],
	"Server Error": ["Internal Error", "Exec Format Error"]
}

def setup_thread():
	timer = threading.Timer(2.0, check_submissions)
	timer.daemon = True
	timer.start()

def get_refined_status(grader_status):
	for item in STATUSES:
		if grader_status in STATUSES[item]:
			return item
		
	return "Server Error"

def check_submissions():
	test_cases_by_grader = { k: [] for k in GRADER_URLS }

	for token in pending_testcases:
		test_cases_by_grader[GRADER_URLS[pending_testcases[token].grader]].append(pending_testcases[token])

	fetch_url = "/submissions/batch?fields=stdout,time,memory,stderr,token,compile_output,message,status&base64_encoded=false&tokens="

	for grader in test_cases_by_grader:
		if len(test_cases_by_grader[grader]) == 0:
			continue

		for index in range(math.ceil(len(test_cases_by_grader[grader]) / 20)):
			paginated_group = test_cases_by_grader[grader][index * 20:index * 20 + 20]
			token_str = ",".join([tc.grader_token for tc in paginated_group])

			response = requests.get(grader + fetch_url + token_str)
			response = response.json()

			for tc in response["submissions"]:
				if tc is None:
					continue

				new_status = get_refined_status(tc["status"]["description"])
				pending_testcases[tc["token"]].status = new_status

				if not new_status == "Pending":
					if "stdout" in tc and tc["stdout"] is not None:
						pending_testcases[tc["token"]].output = tc["stdout"][:100] + ("..." if len(tc["stdout"]) > 100 else "")

					del pending_testcases[tc["token"]]

	setup_thread()

def run_test_cases(submission: Submission):
	global current_grader

	to_submit = { "submissions": [] }

	for test_case in submission.test_cases:
		to_submit["submissions"].append({
			"language_id": submission.language_id,
			"source_code": submission.code,
			"expected_output": test_case.expected_output,
			"stdin": test_case.input
		})

	response = requests.post(GRADER_URLS[current_grader] + "/submissions/batch", json=to_submit)
	response = response.json()

	for i in range(len(response)):
		submission.test_cases[i].grader = current_grader
		submission.test_cases[i].grader_token = response[i]["token"]
		pending_testcases[response[i]["token"]] = submission.test_cases[i]

	current_grader = (current_grader + 1) % len(GRADER_URLS)

@app.post("/create-submission")
async def create_submission(request: Request):
	data = await request.json()

	if not "code" in data or not type(data["code"]) == str or len(data["code"]) == 0:
		return { "error": "No code provided" }

	if not "testcases" in data or not type(data["testcases"]) == list or len(data["testcases"]) == 0:
		return { "error": "No testcases provided" }
	
	if not "language" in data or not type(data["language"]) == int:
		return { "error": "No language provided" }
	
	if not "submission_id" in data:
		return { "error": "No submission id provided" }
	
	submission = Submission(code=data["code"], language_id=data["language"], id=data["submission_id"])
	
	for tc in data["testcases"]:
		if not "input" in tc or not "expected_output" in tc or not "id" in tc:
			return { "error": "Test case does not have expected fields" }
		
		test_case = TestCase(input=tc["input"], expected_output=tc["expected_output"], id=tc["id"])
		submission.add_test_case(test_case)

	current_submissions[submission.id] = submission
	run_test_cases(submission)

	global total_submissions
	total_submissions += 1

@app.post("/get-submission-statuses")
async def get_submission_statuses(request: Request):
	data = await request.json()

	if not "submissions" in data:
		data["submissions"] = []

	to_return = {}

	for sub in data["submissions"]:
		if not sub in current_submissions:
			continue

		to_return[sub] = {}

		for tc in current_submissions[sub].test_cases:
			to_return[sub][tc.id] = {
				"status": tc.status,
				"output": tc.output
			}

	return to_return

@app.get("/status")
def status():
	return {
		"pending_testcases": len(pending_testcases),
		"current_submissions": len(current_submissions),
		"total_submissions": total_submissions
	}

setup_thread()