document.addEventListener("DOMContentLoaded", function() {
    var searchInput = document.getElementById("search-input");
    var userListContainer = document.getElementById("user-list-container");
  
    searchInput.addEventListener("input", function() {
      var searchTerm = searchInput.value.trim();
  
      // Send an AJAX request to the server with the search term
      var xhr = new XMLHttpRequest();
      xhr.open("GET", "/search_user?term=" + searchTerm, true);
      xhr.onreadystatechange = function() {
        if (xhr.readyState === 4 && xhr.status === 200) {
          // Update the user list container with the response
          userListContainer.innerHTML = xhr.responseText;
        }
      };
      xhr.send();
    });
  });