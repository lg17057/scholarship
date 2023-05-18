
function togglePanel(button) {
  button.classList.toggle("active");
  var panel = button.nextElementSibling;
  if (panel.style.display === "block") {
    panel.style.display = "none";
  } else {
    panel.style.display = "block";
  }
}