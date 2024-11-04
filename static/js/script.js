// static/js/script.js
$(document).ready(function () {
  // Toggle menu display
  $(".menu-button").on("click", function () {
    $(".menu").toggle();
  });

  // Hide menu when clicking outside
  $(document).on("click", function (e) {
    if (!$(e.target).closest(".header").length) {
      $(".menu").hide();
    }
  });

  // Click event for video thumbnails
  $(".video-card img").on("click", function () {
    const thumbnail = $(this);
    const loader = thumbnail.siblings(".loader");
    const streamUrl = thumbnail.data("stream-url");

    loader.show();
    thumbnail.closest('.video-card').css("pointer-events", "none");

    // AJAX request to get the download URL
    $.ajax({
      url: "/get-download-url",
      method: "POST",
      contentType: "application/json",
      data: JSON.stringify({ stream_url: streamUrl }),
      success: function (response) {
        loader.hide();
        thumbnail.closest('.video-card').css("pointer-events", "auto");

        if (response.error) {
          alert("Error: " + response.error);
        } else {
          window.open(response, "_blank");
        }
      },
      error: function (xhr, status, error) {
        loader.hide();
        thumbnail.closest('.video-card').css("pointer-events", "auto");
        alert("Failed to get download link: " + (xhr.responseText || error));
      },
    });
  }); // <-- Fermeture de la fonction de clic sur img

  // Gestion du clic sur l'icône de lecture
  $(".play-icon").on("click", function (e) {
    e.stopPropagation();  // Empêche le clic de se propager à l'image de la vidéo
    const playIcon = $(this);
    const loader = playIcon.siblings(".loader");
    const streamUrl = playIcon.data("stream-url");

    loader.show();
    playIcon.css("pointer-events", "none");

    // Requête AJAX pour obtenir l'URL de téléchargement
    $.ajax({
      url: "/get-download-url",
      method: "POST",
      contentType: "application/json",
      data: JSON.stringify({ stream_url: streamUrl }),
      success: function (response) {
        loader.hide();
        playIcon.css("pointer-events", "auto");

        if (response.error) {
          alert("Error: " + response.error);
        } else {
          // Ouvrir l'URL dans une application externe
          window.location.href = `vlc://${response}`;  // Utilise un Custom URL Scheme pour VLC ou autre lecteur
        }
      },
      error: function (xhr, status, error) {
        loader.hide();
        playIcon.css("pointer-events", "auto");
        alert("Failed to get external play link: " + (xhr.responseText || error));
      },
    });
  }); // <-- Fermeture de la fonction de clic sur play-icon

}); // <-- Fermeture de $(document).ready

