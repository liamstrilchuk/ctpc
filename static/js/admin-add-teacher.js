window.addEventListener("load", async () => {
	const data = await fetch("/api/schools");
	const schools = await data.json();
	const boards = {};

	schools.schools.forEach((school) => {
		if (!boards[school.board]) {
			boards[school.board] = [];
		}

		boards[school.board].push(school.name);
	});

	const boardSelect = document.querySelector("select[name=board]");
	const schoolSelect = document.querySelector("select[name=school]");

	Object.keys(boards).forEach((board) => {
		boardSelect.innerHTML += `<option>${board}</option>`;
	});

	boardSelect.addEventListener("change", () => {
		schoolSelect.innerHTML = "";

		boards[boardSelect.value].forEach((school) => {
			schoolSelect.innerHTML += `<option>${school}</option>`;
		})
	});

	boardSelect.dispatchEvent(new CustomEvent("change"));
});