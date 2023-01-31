const dropdown = e => {
  e.preventDefault();
  document.querySelectorAll(".dropdown-content").forEach(x => x.classList.remove("show"));

  console.log(e.currentTarget)
  parent = e.currentTarget;
  console.log(parent.getElementsByClassName('dropdown-content'))
  parent.querySelector(".dropdown-content").classList.toggle('show')
};
const disable = e => { e.preventDefault(); };


// marin i will fucking kill you istg
// only disable the ctx menu for the new note button
document.querySelectorAll(".note#new")[0].addEventListener("contextmenu", disable);
document.querySelector("html").addEventListener("contextmenu", disable);

// disable ctx menu and add a custom drop down for all other notes
document.querySelectorAll(".note:not(#new)").forEach(x => { x.addEventListener("contextmenu", dropdown) });

window.onclick = e => {
  if (!e.target.matches('.note')) {
    var dropdowns = document.getElementsByClassName("dropdown-content");
    var i;
    for (i = 0; i < dropdowns.length; i++) {
      var openDropdown = dropdowns[i];
      if (openDropdown.classList.contains('show')) {
        openDropdown.classList.remove('show');
      }
    }
  }
}

function insertAfter(newNode, existingNode) {
  existingNode.parentNode.insertBefore(newNode, existingNode.nextSibling);
}

function rename_note(id) {
  const note = document.getElementById(id);
  const filename = note.getElementsByClassName("filename")[0];
  let textbox = document.createElement("input");
  textbox.value = filename.innerText;
  document.querySelectorAll(".note:not(#new)").forEach(x => {
    x.removeEventListener("contextmenu", dropdown);
    x.addEventListener("contextmenu", disable);
  });
  textbox.addEventListener("focusout", e => {
    document.querySelectorAll(".note:not(#new)").forEach(x => {
      x.removeEventListener("contextmenu", disable);
      x.addEventListener("contextmenu", dropdown);
    });
    textbox.remove();
    filename.style.display = "inline";
  });
  // disable context menus for all other notes
  textbox.addEventListener("keydown", e => {
    console.log(e.code);
    if (e.code == "Enter") {
      // reenable context menus for all other notes and save
      document.querySelectorAll(".note:not(#new)").forEach(x => {
        x.removeEventListener("contextmenu", disable);
        x.addEventListener("contextmenu", dropdown);
      });

      let newname = textbox.value;
      $.ajax({
        type: "POST",
        url: "/rename",
        dataType: "json",
        data: {
          "id": id,
          "name": newname
        },
        complete: (xhr) => {
          if (xhr.readyState == 4) {
            console.log(xhr.responseText);
            window.location.reload();
          }
        }
      });
      e.currentTarget.remove();
      filename.style.display = "inline";
    }
    else if (e.code == "Escape") {
      document.querySelectorAll(".note:not(#new)").forEach(x => {
        x.removeEventListener("contextmenu", disable);
        x.addEventListener("contextmenu", dropdown);
      });
      e.currentTarget.remove();
      filename.style.display = "inline";
    }
  });
  filename.style.display = "none";
  insertAfter(textbox, filename);
}

function delete_note(id) {
  $.ajax({
    type: "POST",
    url: `/delete/${id}`,
    dataType: "json",
    complete: (xhr) => {
      if (xhr.readyState == 4) {
        console.log(xhr.responseText);
        window.location.reload();
      }
    }
  });
}