#! /usr/bin/env bash

if [[ -z "$1" ]]; then
    echo "usage: $0 1.2.3"
    exit 1
fi

set -euo pipefail

VERSION=$1
SCRIPT_DIR=$(dirname "$0")
RELEASE_DATE=$(date +"%B %-d, %Y")

check_git() {
    if [[ -n "$(git status --porcelain --untracked-files=no)" ]]; then
        echo "Aborting: dirty working directory."
        exit 1
    fi
    if [[ "$(git rev-parse --abbrev-ref HEAD)" != "main" ]]; then
        echo "Aborting: not on main."
        exit 1
    fi
    echo -n "Are you absolutely ready to release? [yN] "
    read confirm
    if [[ ${confirm,,} != "y" ]]; then
        exit 1
    fi
}

update_version() {
    echo -n "Updating mwparserfromhell.__version__..."
    sed -e 's/__version__ = .*/__version__ = "'$VERSION'"/' -i "" src/mwparserfromhell/__init__.py
    echo " done."
}

update_appveyor() {
    filename="appveyor.yml"
    echo -n "Updating $filename..."
    sed -e "s/version: .*/version: $VERSION-b{build}/" -i "" $filename
    echo " done."
}

update_changelog() {
    filename="CHANGELOG"
    echo -n "Updating $filename..."
    sed -e "1s/.*/v$VERSION (released $RELEASE_DATE):/" -i "" $filename
    echo " done."
}

update_docs_changelog() {
    filename="docs/changelog.rst"
    echo -n "Updating $filename..."
    dashes=$(seq 1 $(expr ${#VERSION} + 1) | sed 's/.*/-/' | tr -d '\n')
    previous_lineno=$(expr $(grep -n -e "^---" $filename | sed '2q;d' | cut -d ':' -f 1) - 1)
    previous_version=$(sed $previous_lineno'q;d' $filename)
    sed \
        -e "4s/.*/v$VERSION/" \
        -e "5s/.*/$dashes/" \
        -e "7s/.*/\`Released $RELEASE_DATE <https:\/\/github.com\/earwig\/mwparserfromhell\/tree\/v$VERSION>\`_/" \
        -e "8s/.*/(\`changes <https:\/\/github.com\/earwig\/mwparserfromhell\/compare\/$previous_version...v$VERSION>\`__):/" \
        -i "" $filename
    echo " done."
}

do_git_stuff() {
    echo -n "Git: committing, tagging, and merging release..."
    git commit -qam "release/$VERSION"
    git tag v$VERSION -s -m "version $VERSION"
    echo -n " pushing..."
    git push -q --tags origin main
    echo " done."
}

upload_to_pypi() {
    echo -n "PyPI: uploading source tarball..."
    python setup.py -q sdist
    twine upload dist/mwparserfromhell-$VERSION*
    echo " done."
}

post_release() {
    echo
    echo "*** Release completed."
    echo "*** Update: https://github.com/earwig/mwparserfromhell/releases/tag/v$VERSION"
    echo "*** Verify: https://pypi.org/project/mwparserfromhell"
    echo "*** Verify: https://ci.appveyor.com/project/earwig/mwparserfromhell"
    echo "*** Verify: https://mwparserfromhell.readthedocs.io"
    echo "*** Press enter to sanity-check the release."
    read
}

test_release() {
    echo
    echo "Checking mwparserfromhell v$VERSION..."
    echo -n "Creating a virtualenv..."
    virtdir="mwparser-test-env"
    python -m venv $virtdir
    cd $virtdir
    source bin/activate
    echo " done."
    echo -n "Installing mwparserfromhell with pip..."
    pip -q install --upgrade pip
    pip -q install mwparserfromhell pytest
    echo " done."
    echo -n "Checking version..."
    reported_version=$(python -c 'print(__import__("mwparserfromhell").__version__)')
    if [[ "$reported_version" != "$VERSION" ]]; then
        echo " error."
        echo "*** ERROR: mwparserfromhell is reporting its version as $reported_version, not $VERSION!"
        deactivate
        cd ..
        rm -rf $virtdir
        exit 1
    else
        echo " done."
    fi
    pip -q uninstall -y mwparserfromhell
    echo -n "Downloading mwparserfromhell source tarball..."
    curl -sL "https://pypi.io/packages/source/m/mwparserfromhell/mwparserfromhell-$VERSION.tar.gz" -o "mwparserfromhell.tar.gz"
    echo " done."
    tar -xf mwparserfromhell.tar.gz
    rm mwparserfromhell.tar.gz
    cd mwparserfromhell-$VERSION
    echo "Running unit tests..."
    python setup.py -q install
    python -m pytest
    if [[ "$?" != "0" ]]; then
        echo "*** ERROR: Unit tests failed!"
        deactivate
        cd ../..
        rm -rf $virtdir
        exit 1
    fi
    echo -n "Everything looks good. Cleaning up..."
    deactivate
    cd ../..
    rm -rf $virtdir
    echo " done."
}

echo "Preparing mwparserfromhell v$VERSION..."
cd "$SCRIPT_DIR/.."

check_git
update_version
update_appveyor
update_changelog
update_docs_changelog
do_git_stuff
upload_to_pypi
post_release
test_release

echo "All done."
exit 0
