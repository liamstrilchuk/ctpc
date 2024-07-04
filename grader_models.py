class Submission:
	def __init__(self, id="", code="", language_id=0):
		self.id = id
		self.code = code
		self.test_cases = []
		self.language_id = language_id

	def add_test_case(self, test_case):
		self.test_cases.append(test_case)

class TestCase:
	def __init__(self, id="", input="", expected_output=""):
		self.id = id
		self.input = input
		self.expected_output = expected_output
		self.output = ""
		self.grader = 0
		self.grader_token = ""
		self.status = "Pending"