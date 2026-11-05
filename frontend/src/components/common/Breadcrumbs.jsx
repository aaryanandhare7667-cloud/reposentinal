import React from 'react';
import { Link } from 'react-router-dom';
import { ChevronRight, Home } from 'lucide-react';

export function Breadcrumbs({ items = [] }) {
  return (
    <nav className="flex items-center gap-1.5 text-xs text-text-muted font-mono py-1">
      <Link to="/" className="hover:text-text-primary transition-colors flex items-center gap-1">
        <Home className="w-3.5 h-3.5" />
      </Link>
      {items.map((item, idx) => {
        const isLast = idx === items.length - 1;
        return (
          <React.Fragment key={idx}>
            <ChevronRight className="w-3 h-3 text-text-muted/60" />
            {item.to && !isLast ? (
              <Link to={item.to} className="hover:text-text-primary transition-colors">
                {item.label}
              </Link>
            ) : (
              <span className={`font-medium ${isLast ? 'text-text-primary' : ''}`}>
                {item.label}
              </span>
            )}
          </React.Fragment>
        );
      })}
    </nav>
  );
}
