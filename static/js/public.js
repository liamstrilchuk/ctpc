window.addEventListener("load", () => {
	const toggle = document.getElementById("pub-nav-toggle");
	const links = document.getElementById("pub-nav-links");

	if (!toggle || !links) {
		return;
	}

	toggle.addEventListener("click", () => {
		const isOpen = links.classList.toggle("pub-nav-open");
		toggle.setAttribute("aria-expanded", isOpen ? "true" : "false");
	});

	links.querySelectorAll("a").forEach(link => {
		link.addEventListener("click", () => {
			links.classList.remove("pub-nav-open");
			toggle.setAttribute("aria-expanded", "false");
		});
	});

	document.addEventListener("keydown", event => {
		if (event.key === "Escape") {
			links.classList.remove("pub-nav-open");
			toggle.setAttribute("aria-expanded", "false");
		}
	});
});
