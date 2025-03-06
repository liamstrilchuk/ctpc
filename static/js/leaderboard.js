window.addEventListener("load", () => {
	let problemsHidden = false;
	let virtualHidden = false;

	document.getElementById("toggle-problems").addEventListener("click", () => {
		problemsHidden = !problemsHidden;

		[...document.getElementsByClassName("problem-cell")].forEach(elem => {
			elem.style.display = problemsHidden ? "none" : "table-cell";
		});
	});

	document.getElementById("toggle-virtual").addEventListener("click", () => {
		virtualHidden = !virtualHidden;

		[...document.getElementsByClassName("virtual")].forEach(elem => {
			elem.style.display = virtualHidden ? "none" : "table-row";
		});
	});
});