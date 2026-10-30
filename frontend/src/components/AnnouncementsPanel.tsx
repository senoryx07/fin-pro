import { useState } from "react";

import type { CorporateInfo } from "../types/data";
import { formatDate } from "../utils/format";


interface AnnouncementsPanelProps {
  corporate: CorporateInfo;
}

const INITIAL = 10;


function AnnouncementsPanel({ corporate }: AnnouncementsPanelProps) {
  const [showAll, setShowAll] = useState(false);

  const announcements = showAll
    ? corporate.announcements
    : corporate.announcements.slice(0, INITIAL);


  return (
    <div className="announcements-layout">

      <div className="chart-card">
        <div className="section-label">RECENT ANNOUNCEMENTS</div>

        {announcements.length === 0 && (
          <p className="coverage-text">
            No announcements in the last four months.
          </p>
        )}

        <ul className="announcement-list">
          {announcements.map((a, i) => (
            <li key={`${a.date}-${i}`} className="announcement">
              <div className="announcement-meta">
                <time>{formatDate(a.date)}</time>
                <span className="chip">{a.subject}</span>
              </div>

              {a.text && <p>{a.text}</p>}

              {a.url && (
                <a
                  href={a.url}
                  target="_blank"
                  rel="noreferrer"
                  className="announcement-link"
                >
                  View filing ↗
                </a>
              )}
            </li>
          ))}
        </ul>

        {!showAll && corporate.announcements.length > INITIAL && (
          <button
            className="show-more"
            onClick={() => setShowAll(true)}
          >
            Show all {corporate.announcements.length} announcements
          </button>
        )}
      </div>


      <div className="announcements-side">

        <div className="chart-card">
          <div className="section-label">CORPORATE ACTIONS</div>

          {corporate.actions.length === 0 ? (
            <p className="coverage-text">No corporate actions on record.</p>
          ) : (
            <div className="tech-rows">
              {corporate.actions.map((action, i) => (
                <div key={`${action.ex_date}-${i}`}>
                  <span>{formatDate(action.ex_date)}</span>
                  <strong>{action.purpose}</strong>
                </div>
              ))}
            </div>
          )}
        </div>


        <div className="chart-card">
          <div className="section-label">BOARD MEETINGS</div>

          {corporate.meetings.length === 0 ? (
            <p className="coverage-text">No board meetings on record.</p>
          ) : (
            <ul className="meeting-list">
              {corporate.meetings.map((meeting, i) => (
                <li key={`${meeting.date}-${i}`}>
                  <time>{formatDate(meeting.date)}</time>
                  <p>{meeting.purpose}</p>
                </li>
              ))}
            </ul>
          )}
        </div>

      </div>

    </div>
  );
}


export default AnnouncementsPanel;
