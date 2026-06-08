document.addEventListener('DOMContentLoaded', function () {
	const burger = document.querySelector('.burger');
	const sidebar = document.querySelector('.sidebar');
	if (burger && sidebar) {
		burger.addEventListener('click', function () {
			sidebar.classList.toggle('open');
		});
	}

	document.addEventListener('click', function (event) {
		if (!sidebar) {
			return;
		}
		if (window.innerWidth <= 820 && sidebar.classList.contains('open')) {
			if (!sidebar.contains(event.target) && !(burger && burger.contains(event.target))) {
				sidebar.classList.remove('open');
			}
		}
	});
});
