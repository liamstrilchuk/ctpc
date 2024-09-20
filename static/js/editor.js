window.addEventListener("load", function() {
	const elem = document.getElementById("code-editor");
	const editor = ace.edit(elem);
	editor.session.setMode("ace/mode/python");
	editor.setShowPrintMargin(false);

	const problemSelector = document.getElementById("problem-selector");
	const languageSelector = document.getElementById("language-selector");

	const testCaseContainer = document.getElementById("test-case-container");

	problemSelector.addEventListener("change", async () => {
		testCaseContainer.innerHTML = "";
		const problemId = problemSelector.value;

		if (problemId === "") {
			return;
		}

		const response = await fetch(`/api/test_cases/${problemId}`);
		const json = await response.json();

		for (const testCase of json.test_cases) {
			const testCaseElem = document.createElement("div");
			testCaseElem.classList.add("test-case");
			testCaseElem.innerHTML = `
				<div class="test-case-header">
					<div class="test-case-header-title">Sample Test Case</div>
					<div></div>
				</div>
				<div class="test-case-section-container">
					<div class="test-case-section">
						<div class="test-case-section-title">Input</div>
						<div class="test-case-section-content">${testCase.input}</div>
					</div>
					<div class="test-case-section">
						<div class="test-case-section-title">Expected Output</div>
						<div class="test-case-section-content">${testCase.expected_output}</div>
					</div>
				</div>
			`;
			testCaseContainer.appendChild(testCaseElem);
		}
	});
});