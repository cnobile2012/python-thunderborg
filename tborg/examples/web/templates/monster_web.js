/*
 * monster_web.js
 */

function drive(left, right) {
  var iframe = document.getElementById("set_drive");
  var slider = document.getElementById("speed");
  left *= slider.value / 100.0;
  right *= slider.value / 100.0;
  iframe.src = "/set/" + left + "/" + right;
}

function halt() {
  var iframe = document.getElementById("set_drive");
  iframe.src = "/set/0/0";
}

function photo() {
  var iframe = document.getElementById("set_drive");
  iframe.src = "/photo";
}
