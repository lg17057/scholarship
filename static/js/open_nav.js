function toggleNav() {
  var sidebar = document.getElementById("mySidebar");
  if (sidebar.style.display === "block") {
    closeNav();
  } else {
    openNav();
  }
}

function openNav() {
  var sidebar = document.getElementById("mySidebar");
  sidebar.style.display = "block";
  sidebar.style.animation = "slideIn 0.5s forwards";
}

function closeNav() {
  var sidebar = document.getElementById("mySidebar");
  sidebar.style.animation = "slideOut 0.5s forwards";
  setTimeout(function() {
    sidebar.style.display = "none";
  }, 500);
}

const sidebar = document.getElementById("mySidebar");
const close = document.querySelector(".closebtn");

close.onclick = function() {
  closeNav();
};

window.onclick = function(event) {
  if (event.target === sidebar) {
    closeNav();
  }
};

const sidenav = document.getElementById("mySidenav");
window.addEventListener("click", function(event) {
  if (event.target.closest("#mySidenav") === null) {
    sidenav.style.width = "0";
  }
});


