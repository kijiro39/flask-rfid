function updateClock() {
    var currentTime = new Date();
    var hours = currentTime.getHours();
    var minutes = currentTime.getMinutes();
    var seconds = currentTime.getSeconds();
    var year = currentTime.getFullYear();
    var month = currentTime.getMonth() + 1; // Months are zero-based
    var day = currentTime.getDate();

    // Format the time and date to add leading zeros if necessary
    hours = (hours < 10 ? "0" : "") + hours;
    minutes = (minutes < 10 ? "0" : "") + minutes;
    seconds = (seconds < 10 ? "0" : "") + seconds;
    month = (month < 10 ? "0" : "") + month;
    day = (day < 10 ? "0" : "") + day;
    
    var clockElement = document.getElementById("clock");
    clockElement.innerHTML = hours + ":" + minutes + ":" + seconds + " [" + day + "/" + month + "/" + year + "] ";
}
  
  // Call the updateClock function every second (1000 milliseconds)
  setInterval(updateClock, 1000);