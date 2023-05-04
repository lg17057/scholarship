function goToPreviousDay() {
    let datepicker = document.getElementById("datepicker");
    let currentDate = new Date(datepicker.value);
    let previousDate = new Date(currentDate.getTime() - 86400000); // subtract 1 day (in milliseconds)
    let year = previousDate.getFullYear();
    let month = String(previousDate.getMonth() + 1).padStart(2, "0");
    let day = String(previousDate.getDate()).padStart(2, "0");
    let formattedDate = `${day}-${month}`;
  
    let url = `/rental-logs/${formattedDate}`;
    window.location.href = url;
  }
  
  function goToNextDay() {
    let datepicker = document.getElementById("datepicker");
    let currentDate = new Date(datepicker.value);
    let nextDate = new Date(currentDate.getTime() + 86400000); // add 1 day (in milliseconds)
    let year = nextDate.getFullYear();
    let month = String(nextDate.getMonth() + 1).padStart(2, "0");
    let day = String(nextDate.getDate()).padStart(2, "0");
    let formattedDate = `${day}-${month}`;
  
    let url = `/rental-logs/${formattedDate}`;
    window.location.href = url;
  }