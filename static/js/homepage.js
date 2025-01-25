let navbarActive = false, navbarSide;

window.addEventListener("load", () => {
	const sections = [...document.querySelectorAll(".faq-section")];
	navbarSide = document.getElementById("navbar-side");

	sections.forEach(elem => {
		elem.children[0].addEventListener("click", () => {
			toggleFaq(elem, true);
		});

		toggleFaq(elem, false);
	});

	[
		...document.querySelectorAll("#navbar-side a"),
		document.getElementById("navbar-close-icon"),
		document.getElementById("background")
	].forEach(elem => {
		elem.addEventListener("click", closeNavbarSide);
	});

	document.getElementById("hamburger-icon").addEventListener("click", event => {
		openNavbarSide();
		event.stopPropagation();
	});

	window.addEventListener("resize", () => {
		if (navbarActive) {
			openNavbarSide();
		}
	});
});

function closeNavbarSide() {
	navbarSide.style.left = "100%";
	navbarActive = false;
}

function openNavbarSide() {
	navbarActive = true;
	if (window.innerWidth < 500) {
		navbarSide.style.left = "0px";
		navbarSide.style.width = "100%";
	} else {
		navbarSide.style.left = "calc(100% - 500px)";
		navbarSide.style.width = "500px";
	}
}

function toggleFaq(elem, cascade=false) {
	if (elem.classList.contains("faq-active-section")) {
		elem.classList.remove("faq-active-section");
		elem.children[0].children[1].children[0].style.transform = "rotate(180deg)";
		elem.children[1].style.maxHeight = "0px";
		return;
	}

	if (!cascade) {
		return;
	}

	elem.classList.add("faq-active-section");
	elem.children[0].children[1].children[0].style.transform = "rotate(0deg)";
	elem.children[1].style.maxHeight = elem.children[1].scrollHeight + "px";

	[...document.querySelectorAll(".faq-section")]
		.filter(e => e !== elem)
		.forEach(e => toggleFaq(e));
}