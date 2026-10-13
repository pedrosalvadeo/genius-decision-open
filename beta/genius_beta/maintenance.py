"""Deployment schema and retention commands. Backup/restore live in operations tooling."""
import argparse
from .config import settings
from .db import connect, initialize, purge


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('command',choices=['migrate','purge'])
    args=parser.parse_args()
    c=settings()
    initialize(c['DATABASE'])
    if args.command=='purge':
        db=connect(c['DATABASE'])
        try:
            result = purge(db,c['RETENTION_DAYS'])
            if c['TWIN_ENABLED'] or (c['DATA_DIR'] / 'twins').exists():
                from .twin_integration import purge_twins
                result.update(purge_twins(c, db))
            print(result)
        finally:
            db.close()
    else:
        print('Migrations applied')


if __name__=='__main__':
    main()
