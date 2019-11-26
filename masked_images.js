goog.require('goog.dom');
goog.require('goog.dom.classlist');
goog.require('goog.dom.TagName');
goog.require('goog.events');
goog.require('goog.events.KeyCodes');
goog.require('goog.net.XhrIo');
goog.require("goog.json.Serializer");

class MaskedImagesDispatcher {
    constructor() {
	this.methods = {
	    "add_chat": goog.bind(this.add_chat, this),
	    "show_message": goog.bind(this.show_message, this),
	    "show_logo": goog.bind(this.show_logo, this),
	    "show_answer": goog.bind(this.show_answer, this),
	    "show_all": goog.bind(this.show_all, this),
	}
    }

    /** @param{Message} msg */
    dispatch(msg) {
	this.methods[msg.method](msg);
    }

    /** @param{Message} msg */
    show_message(msg) {
        masked_images.entry.style.display = "none";
        masked_images.clue.style.display = "none";
        masked_images.message.style.display = "initial";
        masked_images.message.innerHTML = msg.text;
    }

    /** @param{Message} msg */
    show_logo(msg) {
        masked_images.entry.style.display = "flex";
        masked_images.entry.style.visibility = "visible";
        masked_images.clue.style.display = "flex";
        masked_images.clueanswer.style.display = "initial";
        masked_images.message.style.display = "none";

        masked_images.logo.src = msg.logo_url;
        masked_images.clueanswer.innerHTML = "\u00a0";
	if (document.activeElement.tagName != "INPUT") masked_images.text.focus();
    }

    /** @param{Message} msg */
    show_answer(msg) {
        masked_images.entry.style.display = "flex";
        masked_images.entry.style.visibility = "hidden";
        masked_images.clue.style.display = "flex";
        masked_images.clueanswer.style.display = "initial";
        masked_images.message.style.display = "none";
        masked_images.logo.src = msg.logo_url;
        masked_images.clueanswer.innerHTML = msg.answer;
    }

    /** @param{Message} msg */
    show_all(msg) {
        masked_images.entry.style.display = "none";
        masked_images.clue.style.display = "none";
        masked_images.clueanswer.style.display = "none";
        masked_images.message.style.display = "flex";

        masked_images.message.innerHTML = "";
        for (var i = 0; i < msg.multi.length; ++i) {
            var div = goog.dom.createDom("DIV", "minidiv",
                                         goog.dom.createDom("IMG", {src: msg.multi[i][0]}),
                                         goog.dom.createTextNode(msg.multi[i][1]));
            masked_images.message.appendChild(div);
        }
    }


    /** @param{Message} msg */
    add_chat(msg) {
	var curr = goog.dom.getChildren(masked_images.chat);
	if (curr.length > 3) {
	    goog.dom.removeNode(curr[0]);
	}
	var el = goog.dom.createDom("P", null, msg.text);
	masked_images.chat.appendChild(el);
    }
}

function masked_images_submit(textel, e) {
    var answer = textel.value;
    if (answer == "") return;
    textel.value = "";
    var username = masked_images.who.value;
    localStorage.setItem("name", username);
    var msg = masked_images.serializer.serialize({"answer": answer, "who": username});
    goog.net.XhrIo.send("/masksubmit", function(e) {
	var code = e.target.getStatus();
	if (code != 204) {
	    alert(e.target.getResponseText());
	}
    }, "POST", msg);
    e.preventDefault();
}

function masked_images_onkeydown(textel, e) {
    if (e.keyCode == goog.events.KeyCodes.ENTER) {
	masked_images_submit(textel, e);
    }
}

var masked_images = {
    waiter: null,
    entry: null,
    message: null,
    text: null,
    who: null,
    chat: null,
    clue: null,
    logo: null,
    clueanswer: null,
    venn: null,
    t6e: null,
    t6a: null,
    words: null,
}

puzzle_init = function() {
    masked_images.serializer = new goog.json.Serializer();

    masked_images.body = goog.dom.getElement("puzz");
    masked_images.entry = goog.dom.getElement("entry");
    masked_images.text = goog.dom.getElement("text");
    masked_images.who = goog.dom.getElement("who");
    masked_images.who.value = localStorage.getItem("name");
    masked_images.chat = goog.dom.getElement("chat");
    masked_images.clue = goog.dom.getElement("clue");
    masked_images.logo = goog.dom.getElement("logo");
    masked_images.clueanswer = goog.dom.getElement("clueanswer");
    masked_images.message = goog.dom.getElement("message");

    goog.events.listen(goog.dom.getElement("text"),
		       goog.events.EventType.KEYDOWN,
		       goog.bind(masked_images_onkeydown, null, masked_images.text));
    goog.events.listen(goog.dom.getElement("masksubmit"),
		       goog.events.EventType.CLICK,
                       goog.bind(masked_images_submit, null, masked_images.text));

    masked_images.waiter = new Common_Waiter(new MaskedImagesDispatcher(), "/maskwait", 0, null, null);
    masked_images.waiter.start();
}

