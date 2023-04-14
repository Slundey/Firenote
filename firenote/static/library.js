// dropdowns
const dropdown = e => {
  e.preventDefault();
  document.querySelectorAll(".dropdown-content").forEach(x => x.classList.remove("show"));

  parent = e.currentTarget;
  parent.querySelector(".dropdown-content").classList.toggle('show')
};
const disable = e => { e.preventDefault(); };

// only disable the ctx menu for the new note button
document.querySelectorAll(".note#new")[0].addEventListener("contextmenu", disable);
document.querySelector("html").addEventListener("contextmenu", disable);

// disable ctx menu and add a custom drop down for all other notes
document.querySelectorAll(".note:not(#new)").forEach(x => { x.addEventListener("contextmenu", dropdown) });

// option and new note modal
var optmodal = document.getElementById("optionsModal");
var optbtn = document.getElementById("optionsBtn");
var optspan = document.getElementsByClassName("close")[0];

optspan.onclick = function () {
  optmodal.style.display = "none";
}

var modal = document.getElementById("noteModal");
var btn = document.getElementById("new");
var span = document.getElementsByClassName("close")[1];
btn.onclick = function () {
  modal.style.display = "block";
}
span.onclick = function () {
  modal.style.display = "none";
}

document.getElementById("sortBtn").addEventListener("click", sortDropdown);

// manages dropdown of sort button
function sortDropdown() {
  document.getElementById("sortDrop").classList.toggle("show");
}

// note edit modal
var editmodal = document.getElementById("editModal");
var editspan = document.getElementsByClassName("close")[2];
var curNoteId; // serves to tell the app that this is the current note being looked at

function edit_menu(id) {
  editmodal.style.display = "block"
  var note = document.getElementById(id)
  var title = note.getAttribute('data-name')
  var desc = note.getAttribute('data-desc')
  var genre = note.getAttribute('data-genre')
  var inputtitle = document.getElementById("editTitle")
  var inputdesc = document.getElementById("editDescription")
  var inputgenre = document.getElementById("editGenre")
  inputtitle.value = title
  inputdesc.value = desc
  inputgenre.value = genre
  curNoteId = id
}
editspan.onclick = function () {
  editmodal.style.display = "none"
}

// settings
function settings_menu(theme, fontsize) {
  optmodal.style.display = "block";
  var inputtheme = document.getElementById("themes")
  var inputsize = document.getElementById("font-size")
  inputtheme.value = theme
  inputsize.value = fontsize
}

// manages modals and dropdowns closing upon clicking in various places
window.onclick = e => {
  if (e.target == optmodal) {
    optmodal.style.display = "none";
  } else if (e.target == modal) {
    modal.style.display = "none";
  } else if (e.target == editmodal) {
    editmodal.style.display = "none";
  } else if (!e.target.matches('.note') && !e.target.matches('#sortBtn')) {
    var dropdowns = document.getElementsByClassName("dropdown-content");
    var i;
    for (i = 0; i < dropdowns.length; i++) {
      var openDropdown = dropdowns[i];
      if (openDropdown.classList.contains('show')) {
        openDropdown.classList.remove('show');
      }
    }
  }
};


// ajax requests
// passes all data needed to make the note to backend
function create_note() {
  let noteid = ""
  $.ajax({
    type: "POST",
    url: `/create`,
    data: {
      "title": $("#title").val(),
      "description": $("#description").val(),
      "genres": $("#genres").val()
    },
    dataType: "json",
    complete: (xhr) => {
      if (xhr.readyState == 4) {
        noteid = xhr.responseText
        window.location.replace(`/editor/${noteid}`)
      }
    }
  })
}

// passes edits to the backend
function edit_note() {
  $.ajax({
    type: "POST",
    url: `/edit`,
    data: {
      "id": curNoteId,
      "title": $("#editTitle").val(),
      "description": $("#editDescription").val(),
      "genre": $("#editGenre").val()
    },
    dataType: "json",
    complete: (xhr) => {
      if (xhr.readyState == 4) {
        window.location.reload()
      }
    }
  })
}

// passes the id to delete to backend
function delete_note(id) {
  $.ajax({
    type: "POST",
    url: `/delete/${id}`,
    dataType: "json",
    complete: (xhr) => {
      if (xhr.readyState == 4) {
        window.location.reload();
      }
    }
  });
}

// passes new settings to backend
function apply_settings() {
  $.ajax({
    type: "POST",
    url: "/apply",
    data: {
      "theme": $("#themes").val(),
      "fontsize": $("#font-size").val()
    },
    dataType: "json",
    complete: (xhr) => {
      if (xhr.readyState == 4) {
        window.location.reload()
      }
    }
  })
}

// tells backend to sort notes by sent genre
function sort(genre) {
  $.ajax({
    type: "POST",
    url: "/sort",
    data: {
      "genre_id": genre
    },
    dataType: "json",
    complete: (xhr) => {
      if (xhr.readyState == 4) {
        window.location.reload()
      }
    }
  })
}
