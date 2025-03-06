window.addEventListener("load", () => {
	let problemsHidden = false;

	document.getElementById("toggle-problems").addEventListener("click", () => {
		problemsHidden = !problemsHidden;

		[...document.getElementsByClassName("problem-cell")].forEach(elem => {
			elem.style.display = problemsHidden ? "none" : "table-cell";
		});
	});
});