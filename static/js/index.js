window.addEventListener("load", () => {
	const timestamps = document.getElementsByClassName("unix-timestamp");

	[...timestamps].forEach((elem) => {
		const timestamp = elem.innerText;
		const date = new Date(timestamp * 1000);
		elem.innerText = date.toDateString() + " " + date.toTimeString().split(" ")[0];
	});

	const durations = document.getElementsByClassName("duration");

	[...durations].forEach((elem) => {
		const duration = Number(elem.innerText);
		const minutes = Math.floor(duration / 60);

		if (minutes < 60) {
			elem.innerText = minutes + 1 + " minute" + (minutes + 1 === 1 ? "" : "s");
		} else if (minutes < 60 * 24) {
			const hours = Math.floor(minutes / 60);
			elem.innerText = hours + " hour" + (hours === 1 ? "" : "s");
		} else {
			const days = Math.floor(minutes / (60 * 24));
			elem.innerText = days + " day" + (days === 1 ? "" : "s");
		}
	});
});