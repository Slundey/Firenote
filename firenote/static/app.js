function markdown(src) {
    var rx_lt = /</g;
    var rx_gt = />/g;
    var rx_space = /\t|\r|\uf8ff/g;
    var rx_escape = /\\([\\\|`*_{}\[\]()#+\-~])/g;
    var rx_hr = /^([*\-=_] *){3,}$/gm;
    var rx_blockquote = /\n *&gt; *([^]*?)(?=(\n|$){2})/g;
    var rx_list = /\n( *)(?:[*\-+]|((\d+)|([a-z])|[A-Z])[.)]) +([^]*?)(?=(\n|$){2})/g;
    var rx_listjoin = /<\/(ol|ul)>\n\n<\1>/g;
    var rx_highlight = /(^|[^A-Za-z\d\\])(([*_])|(~)|(\^)|(--)|(\+\+)|`)(\2?)([^<]*?)\2\8(?!\2)(?=\W|_|$)/g;
    var rx_code = /\n((```|~~~).*\n?([^]*?)\n?\2|((    .*?\n)+))/g;
    var rx_link = /((!?)\[(.*?)\]\((.*?)( ".*")?\)|\\([\\`*_{}\[\]()#+\-.!~]))/g;
    var rx_table = /\n(( *\|.*?\| *\n)+)/g;
    var rx_thead = /^.*\n( *\|( *\:?-+\:?-+\:? *\|)* *\n|)/;
    var rx_row = /.*\n/g;
    var rx_cell = /\||(.*?[^\\])\|/g;
    var rx_heading = /(?=^|>|\n)([>\s]*?)(#{1,6}) (.*?)( #*)? *(?=\n|$)/g;
    var rx_para = /(?=^|>|\n)\s*\n+([^<]+?)\n+\s*(?=\n|<|$)/g;
    var rx_stash = /-\d+\uf8ff/g;

    function replace(rex, fn) {
        src = src.replace(rex, fn);
    }

    function element(tag, content) {
        return '<' + tag + '>' + content + '</' + tag + '>';
    }

    function blockquote(src) {
        return src.replace(rx_blockquote, function (all, content) {
            return element('blockquote', blockquote(highlight(content.replace(/^ *&gt; */gm, ''))));
        });
    }

    function list(src) {
        return src.replace(rx_list, function (all, ind, ol, num, low, content) {
            var entry = element('li', highlight(content.split(
                RegExp('\n ?' + ind + '(?:(?:\\d+|[a-zA-Z])[.)]|[*\\-+]) +', 'g')).map(list).join('</li><li>')));

            return '\n' + (ol
                ? '<ol start="' + (num
                    ? ol + '">'
                    : parseInt(ol, 36) - 9 + '" style="list-style-type:' + (low ? 'low' : 'upp') + 'er-alpha">') + entry + '</ol>'
                : element('ul', entry));
        });
    }

    function highlight(src) {
        return src.replace(rx_highlight, function (all, _, p1, emp, sub, sup, small, big, p2, content) {
            return _ + element(
                emp ? (p2 ? 'strong' : 'em')
                    : sub ? (p2 ? 's' : 'sub')
                        : sup ? 'sup'
                            : small ? 'small'
                                : big ? 'big'
                                    : 'code',
                highlight(content));
        });
    }

    function unesc(str) {
        return str.replace(rx_escape, '$1');
    }

    var stash = [];
    var si = 0;

    src = '\n' + src + '\n';

    replace(rx_lt, '&lt;');
    replace(rx_gt, '&gt;');
    replace(rx_space, '  ');

    // blockquote
    src = blockquote(src);

    // horizontal rule
    replace(rx_hr, '<hr/>');

    // list
    src = list(src);
    replace(rx_listjoin, '');

    // code
    replace(rx_code, function (all, p1, p2, p3, p4) {
        stash[--si] = element('pre', element('code', p3 || p4.replace(/^    /gm, '')));
        return si + '\uf8ff';
    });

    // link or image
    replace(rx_link, function (all, p1, p2, p3, p4, p5, p6) {
        stash[--si] = p4
            ? p2
                ? '<img src="' + p4 + '" alt="' + p3 + '"/>'
                : '<a href="' + p4 + '">' + unesc(highlight(p3)) + '</a>'
            : p6;
        return si + '\uf8ff';
    });

    // table
    replace(rx_table, function (all, table) {
        var sep = table.match(rx_thead)[1];
        return '\n' + element('table',
            table.replace(rx_row, function (row, ri) {
                return row == sep ? '' : element('tr', row.replace(rx_cell, function (all, cell, ci) {
                    return ci ? element(sep && !ri ? 'th' : 'td', unesc(highlight(cell || ''))) : ''
                }))
            })
        )
    });

    // heading
    replace(rx_heading, function (all, _, p1, p2) { return _ + element('h' + p1.length, unesc(highlight(p2))) });

    // paragraph
    replace(rx_para, function (all, content) { return element('p', unesc(highlight(content))) });

    // stash
    replace(rx_stash, function (all) { return stash[parseInt(all)] });

    return src.trim();
};

function tohtml() {
    //html conversion stuff
    fullhtml = "<!DOCTYPE html>\n<html>\n   <head>\n    </head>\n   <body>\n";
    text = document.getElementById("src").value;
    var converter = new showdown.Converter({ noHeaderId: true });
    html = converter.makeHtml(text);
    document.getElementById("preview").innerHTML = html;
    fullhtml = fullhtml.concat(html, "\n    </body>\n</html>")
}

function fileDropdown() {
    document.getElementById("fileDrop").classList.toggle("show");
}

var modal = document.getElementById("optionsModal");
var btn = document.getElementById("optionsBtn");
var span = document.getElementsByClassName("close")[0];
span.onclick = function () {
    modal.style.display = "none";
}
window.onclick = function (event) {
    // Check if the clicked element is the modal
    if (event.target == modal) {
        modal.style.display = "none";
    }

    // Check if the clicked element is not the fileDropbtn
    if (!event.target.matches('#fileDropbtn')) {
        var dropdowns = document.getElementsByClassName("file-dropdown-content");
        var i;
        for (i = 0; i < dropdowns.length; i++) {
            var openDropdown = dropdowns[i];
            if (openDropdown.classList.contains('show')) {
                openDropdown.classList.remove('show');
            }
        }
    }
}

function settings_menu(theme, fontsize) {
    modal.style.display = "block";
    var inputtheme = document.getElementById("themes")
    var inputsize = document.getElementById("font-size")
    inputtheme.value = theme
    inputsize.value = fontsize
  }

function load_fontsize() {
    console.log("HELLO?!?!")
    var area = document.getElementById("src")
    var size = area.getAttribute('data-fontsize')
    area.style.fontSize = "" + size + "px"
}

const src = document.getElementById("src");

const counterfunc = e => {
    let lines = src.value.split("\n");
    let total = 0;
    for (let i = 0; i < lines.length; i++) total += lines[i].length;
    document.getElementById("linecount").innerHTML = lines.length;
    document.getElementById("charcount").innerHTML = total;
};

window.onload = e => {
    counterfunc();
    tohtml();
    load_fontsize();
};
src.oninput = counterfunc;

function save_file(id) {
    let noteid = "";
    $.ajax({
        type: "POST",
        url: "/save",
        data: {
            "id": id,
            "content": $("#src").val()
        },
        dataType: "json",
        complete: (xhr) => {
            if (xhr.readyState == 4) {
                console.log(xhr.responseText);
                noteid = xhr.responseText;
                if (window.location.href.endsWith("/editor")) {
                    console.log(noteid);
                    window.location.replace(`/editor/${noteid}`);
                }
            }
        }
    });
}

function apply_settings() {
    $.ajax({
      type: "POST",
      url: '/apply',
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



