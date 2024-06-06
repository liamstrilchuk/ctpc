window.addEventListener("load", () => {
	const timestamps = document.getElementsByClassName("unix-timestamp");

	[...timestamps].forEach((elem) => {
		const timestamp = elem.innerText;
		const date = new Date(timestamp * 1000);
		elem.innerText = date.toDateString() + " " + date.toTimeString().split(" ")[0];
	});
})