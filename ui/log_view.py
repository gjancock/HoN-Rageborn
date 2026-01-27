import logging

def poll_log_queue(
    *,
    root,
    log_queue,
    log_text,
    formatter,
    interval_ms=100,
):
    """
    Pump LogRecords from queue into Tk Text widget.
    """

    while not log_queue.empty():
        record = log_queue.get()

        msg = formatter.format(record)
        log_text.config(state="normal")

        tag = "INFO"

        if (
            "[FATAL]" in msg
            or "Traceback" in msg
            or "RuntimeError" in msg
            or "Exception" in msg
            or record.levelname in ("ERROR", "CRITICAL")
        ):
            tag = "ERROR"
        elif record.levelname == "WARNING" or "[WARN]" in msg:
            tag = "WARN"

        log_text.insert("end", msg + "\n", tag)
        log_text.see("end")
        log_text.config(state="disabled")

    root.after(
        interval_ms,
        lambda: poll_log_queue(
            root=root,
            log_queue=log_queue,
            log_text=log_text,
            formatter=formatter,
            interval_ms=interval_ms,
        )
    )
