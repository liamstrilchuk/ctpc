window.addEventListener("load", () => {
	let passwordCheck = false, codeCheck = false;
	const forms = {
		password: document.querySelector("input[name=password]"),
		confirm: document.querySelector("input[name=confirm]"),
		code: document.querySelector("input[name=schoolcode]"),
		submit: document.querySelector("input[type=submit]"),
		first: document.querySelector("input[name=first]"),
		last: document.querySelector("input[name=last]"),
		email: document.querySelector("input[name=email]"),
	};

	const updateSubmit = () => {
		forms.submit.disabled = !(passwordCheck && codeCheck && forms.first.value && forms.last.value && forms.email.value);
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
	})

	forms.first.addEventListener("input", updateSubmit);
	forms.last.addEventListener("input", updateSubmit);
	forms.email.addEventListener("input", updateSubmit);

	forms.code.addEventListener("input", () => {
		codeCheck = forms.code.value.match(/^[A-Za-z]{4}-?[A-Za-z]{4}$/) !== null;
		codeCheck && forms.code.classList.remove("input-red");
		updateSubmit();
	});

	forms.code.addEventListener("change", () => {
		codeCheck ? forms.code.classList.remove("input-red") : forms.code.classList.add("input-red");
	})
});