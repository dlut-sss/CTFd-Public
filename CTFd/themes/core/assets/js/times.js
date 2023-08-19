import dayjs from "dayjs";
import advancedFormat from "dayjs/plugin/advancedFormat";
import $ from "jquery";

dayjs.extend(advancedFormat);

export default () => {
  $("[data-time]").each((i, elem) => {
    let $elem = $(elem);
    let time = $elem.data("time");
    let format = $elem.data("time-format") || "MMMMDo, A h:mm:ss";
    elem.innerText = dayjs(time).format(format);
  });
};
