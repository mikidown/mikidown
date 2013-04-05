$(document).ready(function () {
    $(".toc").prepend('<p class="toc-title">TOC</p>');
});

$(".toc").bind("click", function() {
    $(this).children('ul').toggle();
});
