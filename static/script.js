document.addEventListener("DOMContentLoaded", function () {
  // ACTIVATING THE PLAY ICONS ON THE DOM AS MEDIA PLAYERS TO PREVIEW THE TRACK
  const playIcons = document.querySelectorAll(".play-icon");

  playIcons.forEach((playIcon) => {
    playIcon.addEventListener("click", function () {
      const url = this.getAttribute("data-url");

      const audioPlayer = document.getElementById("audio-player");

      audioPlayer.src = url;

      audioPlayer.play();
    });
  });

  // ALERT MESSAGE WHEN USER INPUTS AN INVALID COUNTRY NAME
  document.getElementById("search-country").addEventListener("submit", (event) => {
    const userInput = document.getElementById("user-input").value.toLowerCase();

    // I could not just simply assign a Python list to a JS array. I had to first joint all list items on the Python side with a comma to form a string and the split them with a comma again on the JS side
    const allCountries = document.getElementById("alert-message").getAttribute("data-id").split(',');

    if(!allCountries.includes(userInput)){
      event.preventDefault(); // Prevent the form from submitting
      document.getElementById("alert-message").style.display = "block" // Show the alert message below the input box
    }
  })

});