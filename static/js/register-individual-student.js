window.addEventListener("load", () => {
	const forms = {
		password: document.querySelector("input[name=password]"),
		confirm: document.querySelector("input[name=confirm]"),
		email: document.querySelector("input[name=email]"),
		submit: document.querySelector("input[type=submit]")
	};

	let passwordCheck = false;

	const updateSubmit = () => {
		forms.submit.disabled = !(passwordCheck && forms.email.value.match(/.+@.+\..+/));
	}

	const checkPassword = () => {
		passwordCheck = forms.password.value === forms.confirm.value && forms.password.value.length >= 8;
		forms.password.value === forms.confirm.value && forms.confirm.classList.remove("input-red");
		updateSubmit();
	};

	forms.password.addEventListener("input", checkPassword);
	forms.confirm.addEventListener("input", checkPassword);

	forms.confirm.addEventListener("change", () => {
		forms.password.value === forms.confirm.value ? forms.confirm.classList.remove("input-red") : forms.confirm.classList.add("input-red");
	});

	forms.email.addEventListener("input", updateSubmit);

	updateSubmit();
});