const DEMO_SOLUTIONS = {
	correct: {
		code: "a, b = map(int, input().split())\nprint(a + b)",
		status: "Accepted",
		cssClass: "demo-result-accepted",
		explanation: "Your program read the two numbers and printed their exact sum, matching the expected output of 8."
	},
	offbyone: {
		code: "a, b = map(int, input().split())\nprint(a + b + 1)",
		status: "Wrong Answer",
		cssClass: "demo-result-wrong",
		explanation: "Your program printed 9, but the expected output was 8. A real submission with this result would show you the difference between your output and the expected output."
	},
	infinite: {
		code: "while True:\n\tpass",
		status: "Time Limit Exceeded",
		cssClass: "demo-result-tle",
		explanation: "Your program never finished running. Real submissions had to produce output within a strict time limit."
	}
};

let demoEditor;
let currentSolutionKey = "correct";

window.addEventListener("load", () => {
	const editorElem = document.getElementById("demo-editor");
	if (!editorElem || typeof ace === "undefined") {
		return;
	}

	demoEditor = ace.edit(editorElem);
	demoEditor.setTheme("ace/theme/one_dark");
	demoEditor.session.setMode("ace/mode/python");
	demoEditor.setOptions({ fontSize: "14px", showPrintMargin: false });
	demoEditor.setValue(DEMO_SOLUTIONS.correct.code, -1);

	const buttons = [...document.querySelectorAll(".demo-solution-buttons button")];
	buttons.forEach(button => {
		button.setAttribute("aria-pressed", button.dataset.solution === "correct" ? "true" : "false");

		button.addEventListener("click", () => {
			const key = button.dataset.solution;
			currentSolutionKey = key;
			demoEditor.setValue(DEMO_SOLUTIONS[key].code, -1);
			buttons.forEach(b => b.setAttribute("aria-pressed", b === button ? "true" : "false"));
			hideResult();
		});
	});

	demoEditor.session.on("change", () => {
		buttons.forEach(b => b.setAttribute("aria-pressed", "false"));
	});

	document.getElementById("demo-submit").addEventListener("click", handleDemoSubmit);
});

function matchSolution(code) {
	const trimmed = code.trim();
	for (const key in DEMO_SOLUTIONS) {
		if (DEMO_SOLUTIONS[key].code.trim() === trimmed) {
			return key;
		}
	}
	return null;
}

function hideResult() {
	const resultElem = document.getElementById("demo-result");
	resultElem.hidden = true;
}

function handleDemoSubmit() {
	const submitButton = document.getElementById("demo-submit");
	const resultElem = document.getElementById("demo-result");
	const code = demoEditor.getValue();
	const prefersReducedMotion = window.matchMedia("(prefers-reduced-motion: reduce)").matches;

	submitButton.disabled = true;
	resultElem.hidden = true;

	const showResult = () => {
		const matchedKey = matchSolution(code);
		const solution = matchedKey ? DEMO_SOLUTIONS[matchedKey] : null;

		resultElem.className = "demo-result " + (solution ? solution.cssClass : "demo-result-unknown");
		resultElem.innerHTML = solution
			? `<span class="demo-result-status">Simulated result: ${solution.status}</span>${solution.explanation}`
			: `<span class="demo-result-status">Simulated result: Not recognized</span>This small demo only recognizes the three sample solutions above. Try one of the buttons, or edit the code back to match one of them.`;

		resultElem.hidden = false;
		submitButton.disabled = false;
	};

	if (prefersReducedMotion) {
		showResult();
	} else {
		submitButton.textContent = "Running...";
		setTimeout(() => {
			submitButton.innerHTML = "Submit&nbsp;&nbsp;&rarr;";
			showResult();
		}, 700);
	}
}
