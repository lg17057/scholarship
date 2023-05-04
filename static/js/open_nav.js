
function toggleNav() {
  var sidebar = document.getElementById("mySidebar");
  if (sidebar.style.display === "block") {
    sidebar.style.display = "none";
  } else {
    sidebar.style.display = "block";
  }
}

close.onclick = function() {
         
  sidebar.style.display = "none"
}



window.onclick = function(event) {
  if (event.target == sidebar) {
    sidebar.style.display = "none";
  }
}        


const sidenav = document.getElementById("mySidenav");
window.addEventListener("click", function(event) {
  if (event.target.closest("#mySidenav") === null) {
    sidenav.style.width = "0";
  }
});
