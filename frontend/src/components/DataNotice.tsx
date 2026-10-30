import { useEffect, useState } from "react";

import { loadIndex } from "../services/dataService";
import type { SiteIndex } from "../types/data";
import { formatDate } from "../utils/format";


/** Site-wide reminder that figures are end-of-day, not live. */
function DataNotice() {
  const [index, setIndex] = useState<SiteIndex | null>(null);


  useEffect(() => {
    loadIndex()
      .then(setIndex)
      .catch(() => setIndex(null));
  }, []);


  const updated = index
    ? new Date(index.generated_at).toLocaleString("en-IN", {
        day: "2-digit",
        month: "short",
        hour: "2-digit",
        minute: "2-digit",
      })
    : null;


  return (
    <div className="data-notice" role="note">
      <span className="notice-dot" aria-hidden="true" />
      <span>
        <strong>Not live.</strong> End-of-day data
        {index?.latest_trade_date && (
          <>
            {" "}as of NSE close on{" "}
            <strong>{formatDate(index.latest_trade_date)}</strong>
          </>
        )}
        . Refreshed every trading day after market close.
      </span>
      {updated && (
        <span className="notice-updated">Last updated {updated}</span>
      )}
    </div>
  );
}


export default DataNotice;
