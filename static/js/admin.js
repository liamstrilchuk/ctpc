window.addEventListener("load", async () => {
	const data = await fetch("/api/complete-structure");
	const json = await data.json();

	const boards = json["structure"];
	let allHTML = "";

	boards.forEach((board) => {
		let boardHTML = `<div class="admin-board"><div class="admin-board-controls"><span class="admin-board-name">${board.name}</span></div>`;

		board.schools.forEach((school) => {
			let schoolHTML = `<div class="admin-school"><span class="admin-school-name">${school.name}</span>`;

			schoolHTML += `</div>`;

			boardHTML += schoolHTML;
		})

		boardHTML += `</div>`;

		allHTML += boardHTML;
	});

	document.getElementById("adminContainer").innerHTML = allHTML;
});