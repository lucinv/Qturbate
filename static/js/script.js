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
  });
});

