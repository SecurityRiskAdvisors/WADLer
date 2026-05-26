# 3rd party & native imports
import json
import logging
import time
from rich.console import Console
from rich.logging import RichHandler
from rich.traceback import install

# Internal imports
from wadler.args import Args
from wadler.apitester import APITester
from wadler.wadlparser import WADLParser
from wadler.utils import Utils


def main():
    """
    Waddles all over your APIs
    """

    # Very important stuff
    banner = r"""
              __
          ___( o)>
          \ <_. )
           `---'    the WADLer
"""

    # Setup rich console and logging
    console = Console()
    install(show_locals=True)
    logging.basicConfig(
        level=logging.INFO,
        format="%(message)s",
        datefmt="[%X]",
        handlers=[RichHandler(rich_tracebacks=True, markup=True)],
    )
    log = logging.getLogger("wadl_tester")

    console.print(banner, style="bold")

    # Args & Config
    args_parser = Args(logger=log)
    args = args_parser.run()

    # Set log level
    if args.verbose:
        log.setLevel(logging.DEBUG)

    utils = Utils(logger=log, console=console)

    # Configure session
    session = utils.configure_session(args)

    # Parse WADL
    console.rule("[bold blue]Parsing WADL File[/bold blue]")
    parser = WADLParser(
        wadl_source=args.wadl_source,
        session=session,
        verify_ssl=not args.no_verify_ssl,
        logger=log,
    )
    parser.parse()

    endpoints = parser.get_endpoints()
    log.info(f"Found {len(endpoints)} endpoints in WADL")

    if not endpoints:
        log.warning("No endpoints found in WADL file")
        return

    # Test endpoints
    console.rule("[bold blue]Testing Endpoints[/bold blue]")
    tester = APITester(args=args, session=session, logger=log)

    all_results = []
    for endpoint in endpoints:
        time.sleep(args.sleep)
        results = tester.test_endpoint(parser.base_url, endpoint)
        all_results.extend(results)

    # Generate report
    console.rule("[bold blue]Test Results[/bold blue]")
    utils.generate_report(all_results)

    # Save results if requested
    if args.output:
        utils.save_file(path=args.output, content=all_results)

    return


if __name__ == "__main__":
    main()
