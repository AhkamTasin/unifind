/* Campus Lost & Found — shared client-side behaviour */
document.addEventListener("DOMContentLoaded", function () {
  // Confirm dialogs for any form with a data-confirm attribute
  document.querySelectorAll("form[data-confirm]").forEach(function (form) {
    form.addEventListener("submit", function (e) {
      var msg = form.getAttribute("data-confirm") || "Are you sure?";
      if (!window.confirm(msg)) {
        e.preventDefault();
      }
    });
  });

  // Auto-dismiss alerts after 6 seconds
  document.querySelectorAll(".alert-dismissible").forEach(function (alert) {
    setTimeout(function () {
      if (alert && alert.parentNode) {
        var close = alert.querySelector(".btn-close");
        if (close) close.click();
      }
    }, 6000);
  });

  // Simple client-side password match check on registration
  var p1 = document.querySelector("#id_password1");
  var p2 = document.querySelector("#id_password2");
  if (p1 && p2) {
    p2.addEventListener("input", function () {
      if (p2.value && p1.value !== p2.value) {
        p2.setCustomValidity("Passwords do not match.");
      } else {
        p2.setCustomValidity("");
      }
    });
  }
});
