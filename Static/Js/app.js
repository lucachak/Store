(function () {
  var root = document.documentElement;

  // Mobile navigation
  var menu = document.getElementById("menu-toggle");
  var sidebar = document.getElementById("sidebar");
  if (menu && sidebar) {
    menu.addEventListener("click", function () {
      var open = sidebar.toggleAttribute("data-open");
      menu.setAttribute("aria-expanded", String(open));
    });
  }

  // Theme: dark by default, remembered per browser
  document.querySelectorAll("[data-theme-toggle]").forEach(function (button) {
    button.addEventListener("click", function () {
      var next = root.dataset.theme === "light" ? "dark" : "light";
      root.dataset.theme = next;
      try { localStorage.setItem("theme", next); } catch (e) {}
    });
  });
})();
