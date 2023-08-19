import CTFd from "core/CTFd";
import $ from "jquery";
import dayjs from "dayjs";
import 'dayjs/locale/zh-cn';
import 'dayjs/locale/en';
import advancedFormat from "dayjs/plugin/advancedFormat";
import nunjucks from "nunjucks";
import { Howl } from "howler";
import events from "core/events";
import times from "core/times";
import styles from "../styles";
import { default as helpers } from "core/helpers";

dayjs.extend(advancedFormat);

function getCookieForLanguage(name) {
  const cookies = document.cookie.split('; ');
  for (const cookie of cookies) {
    const [cookieName, cookieValue] = cookie.split('=');
    if (cookieName === name) {
      return decodeURIComponent(cookieValue);
    }
  }
  return null;
}

if (getCookieForLanguage("Scr1wCTFdLanguage") === "en")
{
  dayjs.locale('en')
}else
{
  dayjs.locale('zh-cn')
}

CTFd.init(window.init);
window.CTFd = CTFd;
window.helpers = helpers;
window.$ = $;
window.dayjs = dayjs;
window.nunjucks = nunjucks;
window.Howl = Howl;

$(() => {
  styles();
  times();
  events(CTFd.config.urlRoot);
});
