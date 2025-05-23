let buttonElements, loadingIcons = [];
let isSubmitting = false, submissionId, testCaseResults = [];
let previousSubmissions = [], submissionType, submissionCooldown = new Date();
let editor;
let testCases;
const problemId = location.href.split("/").reverse()[0];

const aceModes = {
	"py": "ace/mode/python",
	"java": "ace/mode/java",
	"c": "ace/mode/c_cpp",
	"cpp": "ace/mode/c_cpp",
	"js": "ace/mode/javascript"
};

window.addEventListener("load", async function() {
	const elem = document.getElementById("code-editor");
	editor = ace.edit(elem);
	editor.setTheme("ace/theme/one_dark");
	editor.setShowPrintMargin(false);
	editor.container.style.lineHeight = 1.4;
	editor.renderer.updateFontSize();

	const rawContent = await fetch("/api/problem/" + problemId);
	const problem = (await rawContent.json());
	const contentElem = document.querySelector("#editor-controls-content");

	testCases = (await (await fetch("/api/test-cases/" + problemId)).json()).test_cases;
	const lastPracticeSubmission = (await (await fetch("/last-practice-submission/" + problemId)).json());
	testCaseResults = lastPracticeSubmission.test_cases;
	testCaseResults.splice(testCases.length);
	editor.setValue(lastPracticeSubmission.code, 1);

	const saved = getSavedLocalCode();
	if (saved && saved.timestamp / 1000 > lastPracticeSubmission.timestamp) {
		editor.setValue(saved.code);
	}

	const submissionData = (await (await fetch("/api/submissions/" + problemId)).json());
	previousSubmissions = submissionData["submissions"];

	buttonElements = {
		selectProblem: document.getElementById("select-problem"),
		selectTestCases: document.getElementById("select-test-cases"),
		selectSubmissions: document.getElementById("select-submissions"),
		selectContest: document.getElementById("select-contest"),
		selectSettings: document.getElementById("select-settings"),
		runSampleTestCases: document.getElementById("run-sample-test-cases"),
		submitSolution: document.getElementById("submit-solution"),
		languageSelector: document.getElementById("language-selector"),
		widthChanger: document.getElementById("width-changer")
	};

	editor.session.setMode(aceModes[buttonElements.languageSelector.value]);
	submissionCooldown = new Date(submissionData["last_submission_time"] * 1000 + 60000);
	
	if (new Date() < submissionCooldown) {
		const loadingIcon = createLoadingIcon(30, "#555", "#fff", 0.7, {
			"type": "progress",
			"start": new Date(submissionData["last_submission_time"] * 1000),
			"end": new Date(submissionData["last_submission_time"] * 1000 + 60000)
		});
		loadingIcon.classList.add("large-loading-icon");
		buttonElements.submitSolution.classList.add("in-progress-button");
		buttonElements.submitSolution.appendChild(loadingIcon);
	}

	buttonElements.languageSelector.value = lastPracticeSubmission.language || "py";

	selectProblem(contentElem, problem);

	buttonElements.selectProblem.addEventListener("click", () => {
		selectProblem(contentElem, problem);
	});

	buttonElements.selectTestCases.addEventListener("click", () => {
		selectTestCases(contentElem, testCases);
	});

	buttonElements.selectSubmissions.addEventListener("click", () => {
		selectSubmissions(contentElem);
	});

	buttonElements.selectContest.addEventListener("click", () => {
		selectContest(contentElem);
	})

	buttonElements.runSampleTestCases.addEventListener("click", () => {
		runSampleTestCases(contentElem, testCases);
	});

	buttonElements.submitSolution.addEventListener("click", () => {
		submitSolution(contentElem);
	});

	let widthChangerSelected = false;

	buttonElements.widthChanger.addEventListener("mousedown", () => {
		widthChangerSelected = true;
	});

	window.addEventListener("mouseup", () => {
		widthChangerSelected = false;
	});

	window.addEventListener("mousemove", (event) => {
		if (widthChangerSelected) {
			const percentage = Math.max(20, Math.min(Math.round(event.clientX / window.innerWidth * 10000) / 100, 80));
			document.getElementById("ace-container").style.width = percentage + "%";
			document.getElementById("editor-controls-container").style.width = (100 - percentage) + "%";
			window.getSelection().removeAllRanges();
		}
	});

	buttonElements.languageSelector.addEventListener("change", () => {
		editor.session.setMode(aceModes[buttonElements.languageSelector.value]);
	});

	window.setInterval(() => {
		const allCode = JSON.parse(localStorage.getItem("editor-code")) || {};
		allCode[problemId] = {
			code: editor.getValue(),
			timestamp: new Date().getTime()
		};
		
		localStorage.setItem("editor-code", JSON.stringify(allCode));
	}, 5000);
});

function getSavedLocalCode() {
	const items = JSON.parse(localStorage.getItem("editor-code")) || {};

	if (Object.keys(items).includes(problemId)) {
		return items[problemId];
	}

	return null;
}

function unselect(button) {
	button.classList.remove("selected");
}

function select(button) {
	button.classList.add("selected");
}

function selectProblem(container, problem) {
	select(buttonElements.selectProblem);
	unselect(buttonElements.selectTestCases);
	unselect(buttonElements.selectSubmissions);
	unselect(buttonElements.selectContest);

	container.innerHTML = `<h1>${problem.title}</h1>` + problem.content;
}

async function selectContest(container) {
	select(buttonElements.selectContest);
	unselect(buttonElements.selectProblem);
	unselect(buttonElements.selectSubmissions);
	unselect(buttonElements.selectTestCases);

	const response = await fetch(`/api/contest/${problemId}`);
	const problemData = await response.json();
	let tableContents = "";

	for (const problem of problemData.problems) {
		let statusHTML = `<span style="color: rgb(183, 184, 199);">Not attempted</span>`;

		if (problem.points_earned === problem.point_value) {
			statusHTML = `<span style="color: rgb(62, 143, 42);">Complete</span>`;
		} else if (problem.points_earned > 0) {
			statusHTML = `<span style="color: rgb(151, 153, 40);">Partially complete</span>`;
		} else if (problem.has_submission) {
			statusHTML = `<span style="color: rgb(183, 184, 199);">Attempted</span>`;
		}

		tableContents += `
			<tr>
				<td><a href="/editor/${problem.id}">${problem.title}</a></td>
				<td>${statusHTML}</td>
				<td>${problem.points_earned}/${problem.point_value}</td>
			</tr>
		`;
	}

	container.innerHTML = `
		<h1>${problemData.contest_name}</h1>
		<div class="table-container">
			<table>
				<tr>
					<th>Problem name</th>
					<th>Status</th>
					<th>Points earned</th>
				</tr>
				${tableContents}
				<tr>
					<th colspan="2">Total</th>
					<th>${problemData.problems.reduce((a, i) => i.points_earned + a, 0)}/${problemData.problems.reduce((a, i) => i.point_value + a, 0)}</th>
				</tr>
			</table>
		</div>
	`;
}

function getDateString(time) {
	const date = new Date(time * 1000);
	return new Date().toLocaleDateString() === date.toLocaleDateString() ? date.toLocaleTimeString() : date.toLocaleString();
}

function setTestCaseStatusHTML(index, container) {
	container.innerHTML = `
		<div class="test-case-status-circle"></div>
		<div>Not yet attempted</div>
	`;

	if (testCaseResults.length === 0 && !(isSubmitting && submissionType === "sample")) {}
	else if (testCaseResults.length <= index && !isSubmitting) {
		return;
	}

	else if ((testCaseResults.length <= index && isSubmitting && submissionType === "sample") || testCaseResults[index].status === "Pending") {
		container.children[0].style.background = "transparent";
		container.children[0].appendChild(createLoadingIcon(16, "#880", "#ff0"));
		container.children[1].innerText = "Running...";
	}

	else {
		const dateString = getDateString(testCaseResults[index].time);
		if (testCaseResults[index].status === "Accepted") {
			container.children[0].style.background = "green";
			container.children[1].innerText = "Accepted at " + dateString;
		} else {
			container.children[0].style.background = "red";
			container.children[1].innerText = testCaseResults[index].status + " at " + dateString;
		}

		if ("output" in testCaseResults[index]) {
			const contentsContainer = container.parentElement.parentElement.parentElement.children[1];

			if (contentsContainer.children.length > 2) {
				contentsContainer.children[2].remove();
			}

			if (testCaseResults[index].status !== "Accepted") {
				if (contentsContainer.children.length === 2) {
					contentsContainer.innerHTML += `
						<div class="test-case-section your-output-section">
							<div class="test-case-section-header">Your output</div>
							<pre class="test-case-section-content">${atob(testCaseResults[index]["output"]).trimEnd()}</pre>
						</div>
					`;
				}
			}
		}
	}
}

function selectTestCases(container, testCases) {
	select(buttonElements.selectTestCases);
	unselect(buttonElements.selectProblem);
	unselect(buttonElements.selectSubmissions);
	unselect(buttonElements.selectContest);

	let testCaseContent = "";

	for (let i = 0; i < testCases.length; i++) {
		const testCase = testCases[i];
		const explanationSection = testCase.explanation ? `
			<div class="test-case-explanation">
				<div class="test-case-section-header">
					Explanation
				</div>
				<pre class="test-case-section-content">${testCase.explanation}</pre>
			</div>
		` : "";

		testCaseContent += `
			<div class="test-case">
				<div class="test-case-header">
					<div>
						<div>${"custom" in testCase ? "Custom" : "Sample"} Test Case #${i + 1}</div>
						<div class="test-case-status"></div>
					</div>
					<div>
						${"custom" in testCase ? `<span class="fa fa-trash custom-delete"></span>` : ""}
					</div>
				</div>
				<div class="test-case-contents-container">
					<div class="test-case-section">
						<div class="test-case-section-header">
							Input
						</div>
						<pre class="test-case-section-content">${testCase.input}</pre>
					</div>
					<div class="test-case-section">
						<div class="test-case-section-header">
							Expected output
						</div>
						<pre class="test-case-section-content">${testCase.expected_output}</pre>
					</div>
				</div>
				${explanationSection}
			</div>
		`;
	}

	container.innerHTML = testCaseContent;
	container.innerHTML += `
		<div class="custom-testcase-container"></div>
		<button class="custom-testcase-button"><span class="fa fa-plus"></span>Create custom test case</button>
	`;

	const customTestcaseButton = document.querySelector(".custom-testcase-button");

	[...document.getElementsByClassName("custom-delete")].forEach(elem => {
		elem.addEventListener("click", () => {
			const index = [...document.getElementsByClassName("test-case")]
				.indexOf(elem.parentElement.parentElement.parentElement);

			testCases.splice(index, 1);
			testCaseResults.splice(index, 1);
			selectTestCases(container, testCases);
		});
	});

	customTestcaseButton.disabled = testCases.length >= 10;
	customTestcaseButton.addEventListener("click", () => {
		[...document.getElementsByClassName("custom-testcase")].forEach(elem => elem.remove());
		const customTestcaseContainer = document.querySelector(".custom-testcase-container");

		customTestcaseContainer.innerHTML += `
			<div class="custom-testcase test-case">
				<div class="test-case-header">
					<div>Create custom test case</div>
				</div>
				<div class="test-case-contents-container">
					<div class="test-case-section">
						<div class="test-case-section-header">
							Input
						</div>
						<pre class="test-case-section-content" contenteditable="true" id="testcase-input">input...</pre>
					</div>
					<div class="test-case-section">
						<div class="test-case-section-header">
							Expected output
						</div>
						<pre class="test-case-section-content" contenteditable="true" id="testcase-output">output...</pre>
					</div>
				</div>
				<div class="test-case-section custom-testcase-buttons">
					<button style="color: rgb(255, 198, 198);" id="testcase-cancel">Cancel</button>
					<button style="color: rgb(214, 255, 198);" id="testcase-add">Add</button>
				</div>
			</div>
		`;

		document.getElementById("testcase-input").focus();
		document.getElementById("testcase-cancel").addEventListener("click", () => {
			customTestcaseContainer.innerHTML = "";
		});
		document.getElementById("testcase-add").addEventListener("click", () => {
			const input = document.getElementById("testcase-input").innerText;
			const expectedOutput = document.getElementById("testcase-output").innerText;
			testCases.push({
				input: input,
				expected_output: expectedOutput,
				custom: true
			});
			customTestcaseContainer.innerHTML = "";
			selectTestCases(container, testCases);
		});
	});

	[...document.querySelectorAll(".test-case-status")].forEach((elem, index) => {
		setTestCaseStatusHTML(index, elem);
	});
}

function selectSubmissions(container) {
	select(buttonElements.selectSubmissions);
	unselect(buttonElements.selectProblem);
	unselect(buttonElements.selectTestCases);
	unselect(buttonElements.selectContest);

	container.innerHTML = "";

	if (previousSubmissions.length === 0) {
		container.innerHTML = `
			<div class="not-submitted">You have not submitted any solutions to this problem yet. Click the arrow above to submit.</div>
		`;
		return;
	}

	for (const sub of previousSubmissions) {
		let submissionHTML = `
			<div class="test-case" data-subid=${sub.id}>
				<div class="test-case-header submission-section-header">
					<div><a href="/submission/${sub.id}" target="_blank" class="submission-link">Submission at ${getDateString(sub.time)}</a></div>
					${sub.status === "Pending" ? "<div class='status-placeholder'></div>" : `<div>${sub.points_earned}/${sub.point_value}</div>`}
				</div>
		`;

		let subtaskCount = 1;
		for (const tcg of sub.test_case_groups) {
			submissionHTML += `
				<div class="submission-section">
					<div class="submission-section-header">
						<div>
							${tcg.is_sample ? "Sample test cases" : "Subtask " + (subtaskCount++)}
						</div>
						<div>${tcg.points_earned}/${tcg.point_value}</div>
					</div>
					<div class="submission-section-content">
			`;

			for (let i = 0; i < tcg.test_cases.length; i++) {
				submissionHTML += `
					<div class="submission-test-case-result">
						<div>
							Test case ${i + 1}
						</div>
						<div class="submission-test-case-icon">
							${tcg.test_cases[i].status === "Pending" ? "<div class='status-placeholder'></div>" : ""}
						</div>
					</div>
				`;
			}

			submissionHTML += "</div></div>";
		}

		container.innerHTML += submissionHTML + "</div>";
	}

	for (let i = 0; i < previousSubmissions.length; i++) {
		updateSubmissionStatus(i);
	}
}

function createLoadingIcon(size, bgColor, color, thickness=1, params={}) {
	const icon = document.createElement("canvas");
	const context = icon.getContext("2d");
	icon.width = size;
	icon.height = size;
	loadingIcons.push({
		context, bgColor, color, frame: 0, size, thickness, params
	});
	return icon;
}

async function runSampleTestCases(container, testcases) {
	if (isSubmitting) {
		return;
	}
	isSubmitting = true;
	submissionType = "sample";

	const testCaseData = testcases;

	const response = await fetch("/submit-practice/" + problemId, {
		method: "POST",
		headers: {
			"Accept": "application/json",
			"Content-Type": "application/json"
		},
		body: JSON.stringify({
			test_cases: testCaseData,
			code: editor.getValue(),
			language: buttonElements.languageSelector.value
		})
	});
	const data = await response.json();

	if ("ratelimit" in data) {
		isSubmitting = false;
		openErrorBox(
			"Could not submit practice submission",
			"Please slow down! You can only submit practice submissions 15 times over 10 minutes."
		);
		return;
	} else if ("error" in data) {
		isSubmitting = false;
		openErrorBox("Could not submit practice submission", data["error"]);
		return;
	}

	selectTestCases(container, testcases);
	submissionId = data.id;

	const loadingIcon = createLoadingIcon(30, "#555", "#fff", 0.7);
	loadingIcon.classList.add("large-loading-icon");
	buttonElements.runSampleTestCases.appendChild(loadingIcon);
	buttonElements.runSampleTestCases.classList.add("in-progress-button");

	[...document.querySelectorAll(".test-case-status")].forEach(elem => {
		elem.children[0].style.background = "transparent";
		elem.children[0].appendChild(createLoadingIcon(16, "#880", "#ff0"));
		elem.children[1].innerText = "Running...";
	});
}

async function submitSolution(container) {
	if (isSubmitting || new Date() < submissionCooldown) {
		return;
	}

	isSubmitting = true;
	submissionType = "submit";

	const formData = new FormData();
	formData.append("language", buttonElements.languageSelector.value);
	formData.append("code", editor.getValue());
	formData.append("return_id", true);

	const response = await fetch("/submit/" + problemId, {
		body: formData,
		method: "POST"
	});

	const data = await response.json();

	if ("error" in data) {
		openErrorBox("Could not submit solution", data["error"]);
		isSubmitting = false;
		return;
	}

	submissionId = data.id;

	previousSubmissions = (await (await fetch("/api/submissions/" + problemId)).json())["submissions"];

	const loadingIcon = createLoadingIcon(30, "#555", "#fff", 0.7);
	loadingIcon.classList.add("large-loading-icon");
	buttonElements.submitSolution.appendChild(loadingIcon);
	buttonElements.submitSolution.classList.add("in-progress-button");
	submissionCooldown = new Date(previousSubmissions[0].time * 1000 + 60000);

	selectSubmissions(container);
}

function openErrorBox(title, error) {
	[...document.getElementsByClassName("error-box")].forEach(elem => elem.remove());

	const box = document.createElement("div");
	box.classList.add("error-box");
	document.body.appendChild(box);

	box.innerHTML = `
		<div class="error-box-title">
			<div>${title}</div>
			<div>
				<span class="fa fa-close error-box-close"></span>
			</div>
		</div>
		<div class="error-box-content">
			${error}<br><br>
			<button class="error-box-close custom-testcase-button">Close</button>
		</div>
	`;

	[...document.getElementsByClassName("error-box-close")].forEach(elem => {
		elem.addEventListener("click", () => {
			[...document.getElementsByClassName("error-box")].forEach(elem => elem.remove());
		});
	});
}

function renderLoadingIcons() {
	for (let i = loadingIcons.length - 1; i > -1; i--) {
		const icon = loadingIcons[i];
		if (!document.body.contains(icon.context.canvas)) {
			loadingIcons.splice(i, 1);
			continue;
		}
		icon.frame++;
		icon.context.clearRect(0, 0, icon.size, icon.size);
		icon.context.lineWidth = icon.size / 8 * icon.thickness;

		icon.context.beginPath();
		icon.context.arc(icon.size / 2, icon.size / 2, icon.size / 2 - 2, 0, Math.PI * 2);
		icon.context.strokeStyle = icon.bgColor;
		icon.context.stroke();

		icon.context.beginPath();
		if (icon.params["type"] && icon.params["type"] === "progress") {
			const percentage = Math.min((new Date() - icon.params["start"]) / (icon.params["end"] - icon.params["start"]), 1);
			icon.context.arc(icon.size / 2, icon.size / 2, icon.size / 2 - 2, -Math.PI / 2, -Math.PI / 2 + Math.PI * 2 * percentage);

			if (percentage >= 1) {
				icon.context.canvas.parentElement.classList.remove("in-progress-button");
				icon.context.canvas.remove();
				loadingIcons.splice(i, 1);
			}
		} else {
			icon.context.arc(icon.size / 2, icon.size / 2, icon.size / 2 - 2, -Math.PI / 2 + icon.frame / 20, icon.frame / 20);
		}
		icon.context.strokeStyle = icon.color;
		icon.context.stroke();
	}

	window.requestAnimationFrame(renderLoadingIcons);
}

renderLoadingIcons();

function updateSubmissionStatus(index) {
	if (previousSubmissions.length <= index) {
		return;
	}
	const submissionElem = document.querySelector("div[data-subid='" + previousSubmissions[index].id + "']");
	if (!submissionElem) {
		return;
	}
	const testCaseElems = [...submissionElem.querySelectorAll(".submission-test-case-result")];
	const groupElems = [...submissionElem.querySelectorAll(".submission-section-header:not(.test-case-header)")];
	const sub = previousSubmissions[index];

	let testCaseNum = 0;
	for (let i = 0; i < sub.test_case_groups.length; i++) {
		const tcg = sub.test_case_groups[i];
		let allDone = true;

		for (const tc of tcg.test_cases) {
			const statusElem = testCaseElems[testCaseNum++].children[1];
			statusElem.innerHTML = "";

			allDone = allDone && tc.status !== "Pending";

			switch (tc.status) {
				case "Pending":
					statusElem.appendChild(createLoadingIcon(16, "#880", "#ff0"));
					break;
				case "Accepted":
					statusElem.innerHTML = `<div class="test-case-status-circle" style="background: green;"></div>`;
					break;
				case "Not Run":
					statusElem.innerHTML = `<div class="test-case-status-desc">${tc.status}</div><div class="test-case-status-circle" style="background: grey;"></div>`;
					break;
				default:
					statusElem.innerHTML = `<div class="test-case-status-desc">${tc.status}</div><div class="test-case-status-circle" style="background: red;"></div>`;
					break;
			}
		}

		groupElems[i].children[1].innerHTML = "";
		if (allDone) {
			if (tcg.point_value > 0) {
				groupElems[i].children[1].innerHTML = `${tcg.points_earned}/${tcg.point_value}`;
			}
		} else {
			groupElems[i].children[1].appendChild(createLoadingIcon(16, "#880", "#ff0"));
		}
	}

	if (sub.status === "Completed") {
		submissionElem.children[0].children[1].innerHTML = `${sub.points_earned}/${sub.point_value}`;
	}
}

window.setInterval(async () => {
	if (!isSubmitting) {
		return;
	}

	if (submissionType === "sample") {
		const response = await fetch("/practice-submission-status/" + submissionId);
		testCaseData = await response.json();
		
		if (testCaseData.filter(tc => tc.status === "Pending").length === 0) {
			isSubmitting = false;
	
			[...buttonElements.runSampleTestCases.querySelectorAll("canvas")].forEach(elem => elem.remove());
			buttonElements.runSampleTestCases.classList.remove("in-progress-button");
		}

		testCaseResults = testCaseData;
		[...document.querySelectorAll(".test-case-status")].forEach((elem, index) => {
			setTestCaseStatusHTML(index, elem);
		});
	} else {
		previousSubmissions = (await (await fetch("/api/submissions/" + problemId)).json())["submissions"];
		updateSubmissionStatus(0);

		if (previousSubmissions[0].status === "Completed") {
			isSubmitting = false;
			[...buttonElements.submitSolution.querySelectorAll("canvas")].forEach(elem => elem.remove());
			const loadingIcon = createLoadingIcon(30, "#555", "#fff", 0.7, {
				"type": "progress",
				"start": new Date(previousSubmissions[0].time * 1000),
				"end": new Date(previousSubmissions[0].time * 1000 + 60000)
			});
			loadingIcon.classList.add("large-loading-icon");
			buttonElements.submitSolution.appendChild(loadingIcon);
		}
	}
}, 2000);