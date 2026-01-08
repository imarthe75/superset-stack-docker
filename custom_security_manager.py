import logging
from superset.security import SupersetSecurityManager
from flask_appbuilder.security.views import AuthDBView
from flask_appbuilder.views import expose
from flask import g, redirect, flash, request
from flask_appbuilder.security.forms import LoginForm_db
from flask_appbuilder.security.views import login_user, get_safe_redirect
from flask_appbuilder.const import AUTH_DB
from authlib.integrations.flask_client import OAuth

class CustomAuthDBView(AuthDBView):
    @expose('/login/', methods=['GET', 'POST'])
    def login(self):
        if g.user is not None and g.user.is_authenticated:
            return redirect(self.appbuilder.get_url_for_index)
        
        form = LoginForm_db()
        if form.validate_on_submit():
            next_url = get_safe_redirect(request.args.get("next", ""))
            user = self.appbuilder.sm.auth_user_db(
                form.username.data, form.password.data
            )
            if not user:
                flash("Invalid login", "warning")
                return redirect(self.appbuilder.get_url_for_login_with(next_url))
            login_user(user, remember=False)
            return redirect(next_url)
        
        # Get OAuth providers for the template
        providers = []
        if hasattr(self.appbuilder.sm, 'oauth_remotes'):
            for name in self.appbuilder.sm.oauth_remotes:
                providers.append({'name': name, 'icon': 'fa-key'})
        
        return self.render_template(
            self.login_template, 
            title=self.title, 
            form=form, 
            appbuilder=self.appbuilder,
            providers=providers
        )

class CustomSecurityManager(SupersetSecurityManager):
    authdbview = CustomAuthDBView

    def register_views(self):
        # By calling FAB's SecurityManager.register_views directly,
        # we bypass Superset's SupersetAuthView (which is a SPA view)
        # and instead use the classic AuthDBView that renders our template.
        from flask_appbuilder.security.sqla.manager import SecurityManager
        SecurityManager.register_views(self)

    def __init__(self, appbuilder):
        super(CustomSecurityManager, self).__init__(appbuilder)
        if self.auth_type == AUTH_DB:
            logging.info("Initializing OAuth providers for Mixed Mode")
            # Manually initialize what FAB would do in AUTH_OAUTH mode
            self.oauth_remotes = {}
            self.oauth = OAuth(appbuilder.app)
            providers = appbuilder.app.config.get("OAUTH_PROVIDERS", [])
            for provider in providers:
                name = provider["name"]
                logging.info(f"Registering OAuth provider for dual-auth: {name}")
                self.oauth.register(name, **provider["remote_app"])
                self.oauth_remotes[name] = self.oauth.create_client(name)
