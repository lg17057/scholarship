
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


