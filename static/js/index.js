window.addEventListener("load", () => {
	const timestamps = document.getElementsByClassName("unix-timestamp");
	const days = document.getElementsByClassName("unix-timestamp-day");

	[...timestamps, ...days].forEach((elem) => {
		const timestamp = elem.innerText;
		const date = new Date(timestamp * 1000);
		if (isNaN(date)) {
			elem.innerText = "Not set";
		} else {
			elem.innerText = date.toDateString() + (elem.className === "unix-timestamp" ? " " + date.toTimeString().split(" ")[0] : "");
		}
	});

	const durations = document.getElementsByClassName("duration");

	[...durations].forEach((elem) => {
		const duration = Number(elem.innerText);
		const minutes = Math.floor(duration / 60);

		if (minutes < 120) {
			elem.innerText = minutes + " minute" + (minutes === 1 ? "" : "s");
		} else if (minutes < 60 * 24) {
			const hours = Math.floor(minutes / 60);
			elem.innerText = hours + " hour" + (hours === 1 ? "" : "s");
		} else {
			const days = Math.floor(minutes / (60 * 24));
			elem.innerText = days + " day" + (days === 1 ? "" : "s");
		}
	});
});