#!/bin/bash
#
# Tagging tests for colorframed.
#
# Usage: ./dotaggingtests.sh [pdflatex|lualatex|all] [file.tex ...]
#
# The default is "all".  Each test file is compiled several times:
#
#   pdflatex: 7 compilations, lualatex: 4 compilations,
#
# and in the last 2 of them the warnings of tagpdf are turned into errors.
# Then tagchecks.py is executed on the PDF.
#
# A text which must be found in the structure tree of the PDF is declared
# in the test file by a line
#
#   % EXPECT: <text>
#
# (several such lines are possible).  This detects text which was typeset
# but not tagged, also when the engine made it an artifact.
#
# A test file expected to fail is marked by a line, anywhere in it,
#
#   % XFAIL: <reason>            (both engines)
#   % XFAIL pdflatex: <reason>   (this engine only; same with lualatex)
#
# Its failure is then reported as XFAIL and does not make the script fail.
# If it passes it is reported as XPASS, which does not make the script
# fail either, but changes the summary.
#
# A summary is written for each engine to testsummary_pdflatex.txt and
# testsummary_lualatex.txt: versions (engine, LaTeX, L3 programming layer,
# colorframed, framed, tagpdf), then for each test its status and the
# output of "tagchecks.py --list".  These two files are
# meant to be committed: at the end, "git diff --quiet" tells whether they
# changed.  They are only written when the default list of test files is
# used (no file argument, no "testonlythose" file); else the summary stays
# in the build directory.
#
# The test files are, by order of priority:
# - those given as arguments,
# - those listed (space separated) in a file "testonlythose",
# - the committed files test_tagging_*.tex (so that new ones can stay in
#   the directory while being worked upon),
# - all files test_tagging_*.tex, if not in a Git repository.
#
# All compilations happen in the directories build_pdflatex and
# build_lualatex, which are emptied first.  The test files are looked for
# in the directory of this script, and so are tagchecks.py and structtree.py.
#
# Environment variables:
#   STYDIR   directory containing colorframed.sty (default: the directory
#            of this script)
#   PYTHON   Python interpreter having pikepdf (default: python3)
#
# Exit status: 0 if all tests pass and no committed summary changed,
#              1 if some test fails,
#              2 if all tests pass but a committed summary changed.

here="$(cd "$(dirname "$0")" && pwd)"
cd "$here" || exit 1

STYDIR="${STYDIR:-$here}"
PYTHON="${PYTHON:-python3}"
export TEXINPUTS="$here:$STYDIR:$TEXINPUTS"

engines="pdflatex lualatex"
case "$1" in
    pdflatex|lualatex) engines="$1"; shift ;;
    all) shift ;;
esac

fullrun=0
if [ $# -gt 0 ]
then
    filelist="$*"
elif [ -f "testonlythose" ]
then
    read -r filelist < "testonlythose"
else
    fullrun=1
fi

if [ $fullrun -eq 0 ]
then
    :
elif git rev-parse --is-inside-work-tree > /dev/null 2>&1
then
    filelist="$(git ls-files 'test_tagging_*.tex')"
else
    filelist="$(ls test_tagging_*.tex 2> /dev/null)"
fi

# test_tagging_10.tex after test_tagging_9.tex, if sort can do it
if [ $fullrun -eq 1 ]
then
    sorted="$(echo "$filelist" | sort -V 2> /dev/null)"
    if [ -n "$sorted" ]
    then
        filelist="$sorted"
    fi
fi

if [ -z "$filelist" ]
then
    echo "No test file."
    exit 1
fi

red="\033[1;31m"
green="\033[32m"
yellow="\033[33m"
off="\033[0m"
starline="******************************************************************************"

# executed before the test file in the last two compilations
towarning='\AddToHook{begindocument/before}{\csname msg_redirect_module:nnn\endcsname{tag}{warning}{error}}'

problem () {
    echo -e "$red"
    echo "$starline"
    echo "**** $1"
    echo -e "$starline$off"
}

# first line matching $2 among the log files of directory $1
logline () {
    cat "$1"/*.log 2> /dev/null | grep -a -m 1 "$2"
}

status=0
summary=""
changed=""

for engine in $engines
do
    case "$engine" in
        pdflatex) nbruns=7 ;;
        lualatex) nbruns=4 ;;
    esac
    dir="build_$engine"
    rm -rf "$dir"
    mkdir "$dir"
    latex="$engine -halt-on-error -interaction=batchmode -output-directory=$dir"
    nboffiles=0
    nbofgoodfiles=0
    nbofbadfiles=0
    nbofxfailfiles=0
    nbofxpassfiles=0
    errorfiles=""
    xpassfiles=""
    results="$dir/results.txt"
    : > "$results"

    for file in $filelist
    do
        ((nboffiles+=1))
        base="$(basename "$file" .tex)"
        xfail=0
        if grep -q -E "^% XFAIL( $engine)?:" "$file"
        then
            xfail=1
            reason="$(grep -m 1 -E "^% XFAIL( $engine)?:" "$file" | sed -E 's/^% XFAIL[^:]*: *//')"
        fi
        ok=1
        why=""
        checks=""
        for ((i = 1; i <= nbruns; i++))
        do
            if [ $i -le $((nbruns - 2)) ]
            then
                $latex "$file" > /dev/null
            else
                $latex "$towarning\\input{$file}" > /dev/null
            fi
            if [ $? -ne 0 ]
            then
                why="fails at compilation $i of $nbruns"
                if [ $i -gt $((nbruns - 2)) ]
                then
                    why="$why (tagpdf warnings are errors)"
                fi
                ok=0
                break
            fi
        done
        if [ $ok -eq 1 ]
        then
            expect=()
            while IFS= read -r text
            do
                expect+=(--expect "$text")
            done < <(sed -n -E 's/^% EXPECT: *//p' "$file")
            checks="$("$PYTHON" tagchecks.py --list "${expect[@]}" "$dir/$base.pdf")"
            checkstatus=$?
            echo "$checks"
            if [ $checkstatus -eq 3 ]
            then
                echo "(structure checks skipped)"
                checks=""
            elif [ $checkstatus -ne 0 ]
            then
                why="fails the checks (tagchecks.py)"
                ok=0
            fi
        fi

        # what is recorded in the summary besides the status line
        if [ -n "$checks" ]
        then
            details="$(echo "$checks" | tail -n +2)"
        else
            details="$(grep -a -m 1 -A 2 '^!' "$dir/$base.log" | sed 's/^/  /')"
        fi

        if [ $ok -eq 1 ] && [ $xfail -eq 0 ]
        then
            ((nbofgoodfiles+=1))
            echo -e "${green}ok: $engine $file$off"
            echo "PASS $file" >> "$results"
            [ -n "$details" ] && echo "$details" >> "$results"
        elif [ $ok -eq 1 ]
        then
            ((nbofxpassfiles+=1))
            xpassfiles="$xpassfiles $file"
            echo -e "${yellow}xpass: $engine $file passes but is marked XFAIL ($reason)$off"
            echo "XPASS $file (marked XFAIL: $reason)" >> "$results"
            [ -n "$details" ] && echo "$details" >> "$results"
        elif [ $xfail -eq 1 ]
        then
            ((nbofxfailfiles+=1))
            echo -e "${yellow}xfail: $engine $file $why ($reason)$off"
            echo "XFAIL $file: $why ($reason)" >> "$results"
            [ -n "$details" ] && echo "$details" >> "$results"
        else
            problem "$engine: $file $why"
            if [ -z "$checks" ]
            then
                grep -a -A 12 '^!' "$dir/$base.log" | head -n 30
            fi
            echo "FAIL $file: $why" >> "$results"
            [ -n "$details" ] && echo "$details" >> "$results"
            status=1
            errorfiles="$errorfiles $file"
            ((nbofbadfiles+=1))
        fi
    done

    counts="FAIL=$nbofbadfiles, PASS=$nbofgoodfiles, XFAIL=$nbofxfailfiles, XPASS=$nbofxpassfiles, TOTAL=$nboffiles"
    line="$engine: $counts"
    for file in $errorfiles
    do
        line="$line\n  fail: $engine $file"
    done
    for file in $xpassfiles
    do
        line="$line\n  xpass: $engine $file"
    done
    summary="$summary$line\n"

    summaryfile="$dir/testsummary_$engine.txt"
    {
        $engine --version | head -n 1
        logline "$dir" '^LaTeX2e <'
        logline "$dir" '^L3 programming layer <'
        logline "$dir" '^Package: colorframed '
        logline "$dir" '^Package: framed '
        logline "$dir" '^Package: tagpdf '
        echo ""
        cat "$results"
        echo ""
        echo "$counts"
    } > "$summaryfile"
    if [ $fullrun -eq 1 ]
    then
        cp "$summaryfile" "testsummary_$engine.txt"
        if ! git ls-files --error-unmatch "testsummary_$engine.txt" > /dev/null 2>&1
        then
            summary="$summary  testsummary_$engine.txt is not committed\n"
        elif ! git diff --quiet -- "testsummary_$engine.txt"
        then
            changed="$changed testsummary_$engine.txt"
            summary="$summary  testsummary_$engine.txt differs from the committed one\n"
        fi
    fi
done

if [ $status -eq 0 ] && [ -n "$changed" ]
then
    status=2
fi

echo ""
if [ $status -eq 0 ]
then
    echo -e "$green$summary$off"
else
    echo -e "$red$summary$off"
fi

exit $status
