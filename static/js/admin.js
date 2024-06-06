window.addEventListener("load", async () => {
	const data = await fetch("/api/complete-structure");
	const json = await data.json();

	const boards = json["structure"];
	let allHTML = "";

	boards.forEach((board) => {
		let boardHTML = `<div class="admin-board"><div class="admin-board-controls"><span class="admin-board-name">${board.name}</span></div>`;

		board.schools.forEach((school) => {
			console.log(school);
			let schoolHTML = `<div class="admin-school"><span class="admin-school-name"><b>${school.name}</b> (<a href="/admin/manage/${school.id}">manage</a>)</span><div class="admin-school-teachers">Teachers: `;

			schoolHTML += school.teachers.map(t => `<a href="/user/${t}">${t}</a>`).join(", ");

			schoolHTML += `</div><div class="admin-school-teams">Teams:<ul>`;
			schoolHTML += school.teams.map(t => `<li>${t.name} (${t.members.length}/6 members)</li>`).join("");
			schoolHTML += `</ul></div></div>`;

			boardHTML += schoolHTML;
		})

		boardHTML += `</div>`;

		allHTML += boardHTML;
	});

	document.getElementById("adminContainer").innerHTML = allHTML;
});