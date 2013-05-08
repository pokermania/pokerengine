MSGFMT=/usr/bin/msgfmt
MSGMERGE=/usr/bin/msgmerge
MSGINIT=/usr/bin/msginit
MSGCONV=/usr/bin/msgconv
MSGFILTER=/usr/bin/msgfilter
XGETTEXT=/usr/bin/xgettext

POTFILES=\
  pokerengine/pokergame.py \
  po/raw.string

DOMAIN=poker-engine

COPYRIGHT_HOLDER=http://www.pokersource.info

MSGID_BUGS_ADDRESS=http://github.com/pokermania/poker-network

POFILES=$(wildcard *.po)
POTFILES_DEP=$(patsubst %,../%,$(POTFILES))
GMOFILES=$(patsubst %.po,%.gmo,$(POFILES))
MOFILES=$(patsubst %.po,../locale/%/LC_MESSAGES/$(DOMAIN).mo,$(POFILES))

all: update-mo

$(DOMAIN).pot: remove-potcdate.sed $(POTFILES_DEP)
	@$(XGETTEXT) \
	    --default-domain=$(DOMAIN) \
	    --directory=.. \
	    --copyright-holder='$(COPYRIGHT_HOLDER)' \
	    --msgid-bugs-address='$(MSGID_BUGS_ADDRESS)' \
	    --no-location \
	    $(POTFILES)
	@if test -f $(DOMAIN).pot ; then \
	    sed -f remove-potcdate.sed < $(DOMAIN).pot > $(DOMAIN).po1 && \
	    sed -f remove-potcdate.sed < $(DOMAIN).po > $(DOMAIN).po2 && \
	    if cmp $(DOMAIN).po{1,2} > /dev/null 2>&1; then \
	        rm -f $(DOMAIN).po $(DOMAIN).po1 $(DOMAIN).po2; \
	    else \
	        rm -f $(DOMAIN).pot $(DOMAIN).po1 $(DOMAIN).po2 && \
	        mv $(DOMAIN).po $(DOMAIN).pot; \
	    fi; \
	else \
	    mv $(DOMAIN).po $(DOMAIN).pot; \
	fi

%.po: $(DOMAIN).pot
	@#echo -n "msgmerge $@ "
	@$(MSGMERGE) -qU $@ poker-engine.pot
	@#sed -i -f remove-potcdate.sed $@

%.gmo: %.po
	@#echo msgfmt $@
	@$(MSGFMT) -v -c --statistics -o $@ $<

../locale/%/LC_MESSAGES/$(DOMAIN).mo: %.gmo
	@mkdir -p `dirname "$@"`
	@cp $< $@

update-gmo: $(GMOFILES)

update-mo: $(MOFILES)

clean:
	rm -rf poker-engine.po poker-engine.po1 poker-engine.po2 locale *.gmo *~

